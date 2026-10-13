import "server-only";
import Anthropic from "@anthropic-ai/sdk";
import { betaZodOutputFormat } from "@anthropic-ai/sdk/helpers/beta/zod";
import { env } from "./env";
import { legalAnalysisSchema, type LegalAnalysis } from "./analysis-schema";
import { SYSTEM_PROMPT, jurisdictionBlock, userInstructions } from "./prompts";
import type { JurisdictionRow } from "./types";

let client: Anthropic | null = null;
function anthropic(): Anthropic {
  if (!client) client = new Anthropic({ apiKey: env.anthropicApiKey() });
  return client;
}

// USD per million tokens. Cache writes with 1h TTL bill at 2x input.
const PRICING: Record<string, { input: number; output: number; cacheRead: number }> = {
  "claude-opus-5-5": { input: 4, output: 20, cacheRead: 0.2 },
  "claude-sonnet-5-5": { input: 2, output: 10, cacheRead: 0.2 },
};

export interface AnalysisInput {
  fileName: string;
  countryCode: string;
  documentType: string;
  language: string;
  pageCount: number | null;
  /** Extracted text. When empty, `pdfBase64` is sent instead (scanned PDF). */
  text: string | null;
  pdfBase64: string | null;
  jurisdiction: JurisdictionRow[];
}

export interface AnalysisOutput {
  result: LegalAnalysis;
  model: string;
  usage: Record<string, unknown>;
  costUsd: number | null;
}

export class AnalysisRefusedError extends Error {}

export async function analyzeDocument(input: AnalysisInput): Promise<AnalysisOutput> {
  const model = env.anthropicModel();
  const scanned = !input.text;

  const documentBlock: Anthropic.Beta.BetaContentBlockParam = scanned
    ? {
        type: "document",
        source: { type: "base64", media_type: "application/pdf", data: input.pdfBase64! },
      }
    : {
        type: "document",
        source: { type: "text", media_type: "text/plain", data: input.text! },
        title: input.fileName,
      };

  const response = await anthropic().beta.messages.parse({
    model,
    max_tokens: 16000,
    betas: ["server-side-fallback-2026-07-01"],
    // On a safety-classifier refusal the API retries on a fallback model in the same call.
    fallbacks: "default",
    output_config: {
      effort: env.anthropicEffort(),
      format: betaZodOutputFormat(legalAnalysisSchema),
    },
    // Prompt caching: tools → system → messages. The frozen instructions and the
    // per-jurisdiction legislation block form a stable prefix; the breakpoint on
    // the last system block caches both for 1h across all users of that country/type.
    system: [
      { type: "text", text: SYSTEM_PROMPT },
      {
        type: "text",
        text: jurisdictionBlock(input.countryCode, input.documentType, input.jurisdiction),
        cache_control: { type: "ephemeral", ttl: "1h" },
      },
    ],
    messages: [
      {
        role: "user",
        content: [
          documentBlock,
          {
            type: "text",
            text: userInstructions({
              fileName: input.fileName,
              language: input.language,
              pageCount: input.pageCount,
              scanned,
            }),
          },
        ],
      },
    ],
  });

  if (response.stop_reason === "refusal") {
    throw new AnalysisRefusedError(
      `The model declined to analyse this document${response.stop_details?.category ? ` (${response.stop_details.category})` : ""}.`,
    );
  }
  if (response.stop_reason === "max_tokens") {
    throw new Error("Analysis was cut off (max_tokens). Try a shorter document.");
  }
  if (!response.parsed_output) {
    throw new Error("The model did not return a valid structured analysis.");
  }

  const u = response.usage;
  const usage = {
    input_tokens: u.input_tokens,
    output_tokens: u.output_tokens,
    cache_creation_input_tokens: u.cache_creation_input_tokens ?? 0,
    cache_read_input_tokens: u.cache_read_input_tokens ?? 0,
  };

  const price = PRICING[response.model];
  const costUsd = price
    ? (usage.input_tokens * price.input +
        usage.cache_creation_input_tokens * price.input * 2 +
        usage.cache_read_input_tokens * price.cacheRead +
        usage.output_tokens * price.output) /
      1_000_000
    : null;

  return { result: response.parsed_output, model: response.model, usage, costUsd };
}
