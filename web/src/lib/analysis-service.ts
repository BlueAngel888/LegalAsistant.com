import "server-only";
import { createHash } from "node:crypto";
import { analyzeDocument, AnalysisRefusedError } from "./claude";
import { PROMPT_VERSION } from "./analysis-schema";
import {
  findCachedAnalysis,
  getJurisdictionData,
  insertAnalysis,
  updateDocument,
} from "./db";
import { downloadFile } from "./storage";
import { MIN_TEXT_CHARS } from "./pdf";
import type { DocumentRow } from "./types";

export function cacheKeyFor(doc: Pick<DocumentRow, "text_hash" | "country_code" | "document_type" | "language">) {
  return createHash("sha256")
    .update([doc.text_hash, doc.country_code, doc.document_type, doc.language, PROMPT_VERSION].join("|"))
    .digest("hex");
}

/**
 * Runs the full analysis for one document and stores the result.
 * Cost control, cheapest first:
 *   1. Result cache: identical file + jurisdiction + type + language + prompt
 *      version reuses a stored analysis (zero API calls).
 *   2. Prompt cache: system prompt + jurisdiction block are cached by the API.
 *   3. Text over PDF: we send extracted text; the PDF itself only for scans.
 */
export async function runAnalysis(
  doc: DocumentRow,
  opts: { skipResultCache?: boolean } = {},
): Promise<void> {
  const cacheKey = cacheKeyFor(doc);
  try {
    const cached = opts.skipResultCache ? null : await findCachedAnalysis(cacheKey);
    if (cached) {
      await insertAnalysis({
        document_id: doc.id,
        user_id: doc.user_id,
        cache_key: cacheKey,
        model: cached.model,
        prompt_version: PROMPT_VERSION,
        result: cached.result,
        usage: null,
        cost_usd: 0,
        from_cache: true,
      });
      await updateDocument(doc.id, { status: "analyzed", error_message: null });
      return;
    }

    const text = doc.extracted_text && doc.extracted_text.length >= MIN_TEXT_CHARS ? doc.extracted_text : null;
    const pdfBase64 = text ? null : Buffer.from(await downloadFile(doc.storage_path)).toString("base64");
    const jurisdiction = await getJurisdictionData(doc.country_code, doc.document_type);

    const out = await analyzeDocument({
      fileName: doc.file_name,
      countryCode: doc.country_code,
      documentType: doc.document_type,
      language: doc.language,
      pageCount: doc.page_count,
      text,
      pdfBase64,
      jurisdiction,
    });

    await insertAnalysis({
      document_id: doc.id,
      user_id: doc.user_id,
      cache_key: cacheKey,
      model: out.model,
      prompt_version: PROMPT_VERSION,
      result: out.result,
      usage: out.usage,
      cost_usd: out.costUsd,
      from_cache: false,
    });
    await updateDocument(doc.id, { status: "analyzed", error_message: null });
  } catch (err) {
    console.error("[analysis] failed", doc.id, err);
    const message =
      err instanceof AnalysisRefusedError
        ? err.message
        : "Analysis failed. Please try again; if it keeps failing, contact support.";
    await updateDocument(doc.id, { status: "failed", error_message: message }).catch(() => {});
  }
}
