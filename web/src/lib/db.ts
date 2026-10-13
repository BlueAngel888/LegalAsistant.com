import "server-only";
import { supabaseAdmin } from "./supabase";
import type {
  AnalysisRow,
  DocumentRow,
  DocumentSummary,
  JurisdictionRow,
} from "./types";

const SUMMARY_COLUMNS =
  "id, user_id, file_name, mime_type, size_bytes, page_count, text_hash, country_code, document_type, language, status, error_message, created_at, updated_at";

export async function listDocuments(userId: string): Promise<DocumentSummary[]> {
  const { data, error } = await supabaseAdmin()
    .from("documents")
    .select(SUMMARY_COLUMNS)
    .eq("user_id", userId)
    .order("created_at", { ascending: false });
  if (error) throw new Error(error.message);
  return (data ?? []) as DocumentSummary[];
}

export async function getDocument(
  userId: string,
  id: string,
): Promise<DocumentRow | null> {
  const { data, error } = await supabaseAdmin()
    .from("documents")
    .select("*")
    .eq("id", id)
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as DocumentRow | null;
}

export async function updateDocument(
  id: string,
  patch: Partial<DocumentRow>,
): Promise<void> {
  const { error } = await supabaseAdmin()
    .from("documents")
    .update(patch)
    .eq("id", id);
  if (error) throw new Error(error.message);
}

export async function getLatestAnalysis(
  userId: string,
  documentId: string,
): Promise<AnalysisRow | null> {
  const { data, error } = await supabaseAdmin()
    .from("analysis_results")
    .select("*")
    .eq("document_id", documentId)
    .eq("user_id", userId)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as AnalysisRow | null;
}

/** Any previous analysis with the same cache key (same file, jurisdiction, type, language, prompt). */
export async function findCachedAnalysis(
  cacheKey: string,
): Promise<AnalysisRow | null> {
  const { data, error } = await supabaseAdmin()
    .from("analysis_results")
    .select("*")
    .eq("cache_key", cacheKey)
    .eq("from_cache", false)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as AnalysisRow | null;
}

export async function insertAnalysis(
  row: Omit<
    AnalysisRow,
    "id" | "created_at" | "review_status" | "reviewer_notes" | "reviewed_at"
  >,
): Promise<AnalysisRow> {
  const { data, error } = await supabaseAdmin()
    .from("analysis_results")
    .insert(row)
    .select("*")
    .single();
  if (error) throw new Error(error.message);
  return data as AnalysisRow;
}

export async function getJurisdictionData(
  countryCode: string,
  documentType: string,
): Promise<JurisdictionRow[]> {
  const { data, error } = await supabaseAdmin()
    .from("jurisdiction_data")
    .select(
      "country_code, country_name, document_type, title, reference, summary, source_url, verified",
    )
    .eq("country_code", countryCode)
    .or(`document_type.is.null,document_type.eq.${documentType}`)
    // Stable order keeps the cached prompt prefix byte-identical.
    .order("document_type", { ascending: true, nullsFirst: true })
    .order("reference", { ascending: true });
  if (error) throw new Error(error.message);
  return (data ?? []) as JurisdictionRow[];
}
