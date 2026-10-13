import { z } from "zod";

// Bump when the prompt or schema changes so cached results are not reused.
export const PROMPT_VERSION = "2026-10-12.v1";

const level = z.enum(["low", "medium", "high"]);

const legalPoint = z.object({
  title: z.string().describe("Short headline of the point"),
  explanation: z.string().describe("Why it matters, in plain language, quoting the document where useful"),
  legal_basis: z.string().describe("Article/law it relies on, or 'unspecified' if none applies with confidence"),
});

export const legalAnalysisSchema = z.object({
  summary: z.string().describe("3-6 sentence plain-language summary of the document and the user's position"),
  document_type_detected: z.string(),
  jurisdiction: z.string().describe("Country (and region if relevant) whose law was applied"),
  parties: z.array(z.object({ name: z.string(), role: z.string() })),
  key_dates: z.array(z.object({ date: z.string(), description: z.string() })),
  strengths: z.array(legalPoint).describe("Points that favour the user"),
  weaknesses: z.array(legalPoint).describe("Points that work against the user"),
  potential_errors: z
    .array(legalPoint.extend({ severity: level }))
    .describe("Procedural or substantive errors, missing mandatory elements, possible nullity grounds"),
  defense_strategies: z.array(
    z.object({
      title: z.string(),
      steps: z.array(z.string()),
      legal_basis: z.string(),
      likelihood_of_success: level,
    }),
  ),
  deadlines_and_actions: z.array(
    z.object({ action: z.string(), deadline: z.string(), urgency: level }),
  ),
  legal_references: z.array(z.object({ reference: z.string(), relevance: z.string() })),
  risk_level: level.describe("Overall risk for the user"),
  confidence: level.describe("How confident the analysis is, given document quality and legal certainty"),
  missing_information: z.array(z.string()).describe("Facts or documents needed for a firmer conclusion"),
  disclaimer: z.string(),
});

export type LegalAnalysis = z.infer<typeof legalAnalysisSchema>;
