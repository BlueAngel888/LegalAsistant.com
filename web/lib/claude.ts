import Anthropic from '@anthropic-ai/sdk';
import { ClaudeAnalysisOutput, Jurisdiction, DocumentType } from './types';

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

Always respond in valid JSON format.`;

const ANALYSIS_TEMPLATE = `Analyze the following legal document and provide a comprehensive analysis in JSON format:

Document Content:
{DOCUMENT_CONTENT}

Language: {LANGUAGE}
Suggested Jurisdiction: {JURISDICTION}

Respond ONLY with a valid JSON object (no markdown, no code blocks) with this exact structure:
{
  "jurisdiction": "Jurisdiction code (EU_RO, USA_CA, etc.)",
  "documentType": "CONTRACT|NDA|EMPLOYMENT|LEASE|POLICY|TERMS_OF_SERVICE|PRIVACY_POLICY|OTHER",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1", "weakness 2", ...],
  "legalErrors": ["error 1", "error 2", ...],
  "defenseStrategy": ["strategy 1", "strategy 2", ...],
  "riskLevel": "LOW|MEDIUM|HIGH|CRITICAL",
  "summary": "2-3 sentence summary",
  "recommendations": ["recommendation 1", "recommendation 2", ...]
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
      .replace('{LANGUAGE}', language)
      .replace('{JURISDICTION}', jurisdiction || 'AUTO_DETECT');

    const response = await client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 2048,
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
      strengths: Array.isArray(data.strengths) ? data.strengths : [],
      weaknesses: Array.isArray(data.weaknesses) ? data.weaknesses : [],
      legalErrors: Array.isArray(data.legalErrors) ? data.legalErrors : [],
      defenseStrategy: Array.isArray(data.defenseStrategy) ? data.defenseStrategy : [],
      riskLevel: (data.riskLevel || 'MEDIUM') as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
      summary: data.summary || '',
      recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
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
