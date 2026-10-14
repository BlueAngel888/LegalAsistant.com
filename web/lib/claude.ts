import Anthropic from '@anthropic-ai/sdk';
import { ClaudeAnalysisOutput, Jurisdiction, DocumentType } from './types';
import { localeInfo, matchLocale } from './i18n/config';
import { toAnalysisPoints } from './analysis-points';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
});

const SYSTEM_PROMPT = `You are an expert legal document analyzer with deep knowledge of:
- Contract law across EU jurisdictions (Germany, France, Italy, Spain, Romania, Netherlands, Belgium, Austria, Sweden)
- US contract law (Federal, New York, California, Texas)
- Document types: contracts, NDAs, employment agreements, leases, policies, terms of service, privacy policies

Your task is to analyze legal documents and provide:
1. Jurisdiction detection
2. Document type classification
3. Strengths and weaknesses analysis
4. Legal errors and issues
5. Defense strategy recommendations
6. Risk assessment
7. Actionable recommendations

Tie every point you make to the specific law it rests on (article and act, e.g. "art. 1.823 Cod civil" or "Cal. Civ. Code § 1950.5"), and for each clause you assess say whether it complies with that law. Cite only provisions you are confident exist and apply in the detected jurisdiction; when you are not sure of the exact article, name the act and mark the clause UNCLEAR rather than inventing a citation.

Always respond in valid JSON format.`;

const ANALYSIS_TEMPLATE = `Analyze the following legal document and provide a comprehensive analysis in JSON format:

Document Content:
{DOCUMENT_CONTENT}

Suggested Jurisdiction: {JURISDICTION}

Write every human-readable value (each "text", and the summary) in {LANGUAGE}, whatever language the document itself is written in. Write each "legalBasis" as the citation is normally written in the jurisdiction (e.g. "art. 1.823 Cod civil" for Romania). Keep the JSON keys and the jurisdiction, documentType, riskLevel and status codes exactly as specified below, in English.

Every point is an object:
- "text": the finding, one or two sentences.
- "legalBasis": the article and act it relies on; empty string only when no specific law applies.
- "status" (strengths, weaknesses and legalErrors only): COMPLIANT if the clause is valid under that law, NON_COMPLIANT if it breaches it, UNCLEAR if its validity depends on facts or case law you cannot confirm.

Respond ONLY with a valid JSON object (no markdown, no code blocks) with this exact structure:
{
  "jurisdiction": "Jurisdiction code (EU_RO, USA_CA, etc.)",
  "documentType": "CONTRACT|NDA|EMPLOYMENT|LEASE|POLICY|TERMS_OF_SERVICE|PRIVACY_POLICY|OTHER",
  "strengths": [{"text": "...", "legalBasis": "...", "status": "COMPLIANT|NON_COMPLIANT|UNCLEAR"}, ...],
  "weaknesses": [{"text": "...", "legalBasis": "...", "status": "COMPLIANT|NON_COMPLIANT|UNCLEAR"}, ...],
  "legalErrors": [{"text": "...", "legalBasis": "...", "status": "COMPLIANT|NON_COMPLIANT|UNCLEAR"}, ...],
  "defenseStrategy": [{"text": "...", "legalBasis": "..."}, ...],
  "riskLevel": "LOW|MEDIUM|HIGH|CRITICAL",
  "summary": "2-3 sentence summary",
  "recommendations": [{"text": "...", "legalBasis": "..."}, ...]
}`;

interface CacheConfig {
  enabled: boolean;
  ttlMinutes: number;
}

const cacheConfig: CacheConfig = {
  enabled: process.env.ENABLE_PROMPT_CACHING === 'true',
  ttlMinutes: parseInt(process.env.CACHE_TTL_MINUTES || '5', 10),
};

export async function analyzeDocument(
  documentContent: string,
  language: string = 'en',
  jurisdiction?: Jurisdiction,
): Promise<ClaudeAnalysisOutput> {
  try {
    if (!process.env.ANTHROPIC_API_KEY) {
      throw new Error('ANTHROPIC_API_KEY not configured');
    }

    const userMessage = ANALYSIS_TEMPLATE
      .replace('{DOCUMENT_CONTENT}', documentContent.substring(0, 12000))
      .replace('{LANGUAGE}', languageName(language))
      .replace('{JURISDICTION}', jurisdiction || 'AUTO_DETECT');

    const response = await client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      system: [
        {
          type: 'text',
          text: SYSTEM_PROMPT,
          ...(cacheConfig.enabled && {
            cache_control: { type: 'ephemeral' },
          }),
        },
      ],
      messages: [
        {
          role: 'user',
          content: userMessage,
        },
      ],
    });

    const analysisText =
      response.content[0].type === 'text' ? response.content[0].text : '';

    const analysis = parseAnalysisResponse(analysisText);

    return analysis;
  } catch (error) {
    console.error('Error analyzing document with Claude:', error);
    throw new Error(`Document analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

function languageName(language: string): string {
  const locale = matchLocale(language);
  return locale ? localeInfo[locale].englishName : language;
}

function parseAnalysisResponse(responseText: string): ClaudeAnalysisOutput {
  try {
    let jsonStr = responseText.trim();

    if (jsonStr.startsWith('```json')) {
      jsonStr = jsonStr.replace(/^```json\s*/, '').replace(/\s*```$/, '');
    } else if (jsonStr.startsWith('```')) {
      jsonStr = jsonStr.replace(/^```\s*/, '').replace(/\s*```$/, '');
    }

    const data = JSON.parse(jsonStr);

    return {
      jurisdiction: (data.jurisdiction || 'UNKNOWN') as Jurisdiction,
      documentType: (data.documentType || 'OTHER') as DocumentType,
      strengths: toAnalysisPoints(data.strengths),
      weaknesses: toAnalysisPoints(data.weaknesses),
      legalErrors: toAnalysisPoints(data.legalErrors),
      defenseStrategy: toAnalysisPoints(data.defenseStrategy),
      riskLevel: (data.riskLevel || 'MEDIUM') as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
      summary: data.summary || '',
      recommendations: toAnalysisPoints(data.recommendations),
    };
  } catch (error) {
    console.error('Failed to parse Claude response:', error);
    return {
      jurisdiction: Jurisdiction.UNKNOWN,
      documentType: DocumentType.OTHER,
      strengths: [],
      weaknesses: [],
      legalErrors: [],
      defenseStrategy: [],
      riskLevel: 'MEDIUM',
      summary: 'Analysis could not be completed properly.',
      recommendations: [],
    };
  }
}

export function isCachingEnabled(): boolean {
  return cacheConfig.enabled;
}

export function getCacheTTL(): number {
  return cacheConfig.ttlMinutes;
}
