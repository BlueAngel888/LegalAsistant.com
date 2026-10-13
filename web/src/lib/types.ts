import type { LegalAnalysis } from "./analysis-schema";

export type DocumentStatus = "uploaded" | "processing" | "analyzed" | "failed";

export interface DocumentRow {
  id: string;
  user_id: string;
  file_name: string;
  storage_path: string;
  mime_type: string;
  size_bytes: number;
  page_count: number | null;
  extracted_text: string | null;
  text_hash: string | null;
  country_code: string;
  document_type: string;
  language: string;
  status: DocumentStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

/** Documents as returned to the client (no full text, no storage path). */
export type DocumentSummary = Omit<DocumentRow, "extracted_text" | "storage_path">;

export interface AnalysisRow {
  id: string;
  document_id: string;
  user_id: string;
  cache_key: string;
  model: string;
  prompt_version: string;
  result: LegalAnalysis;
  usage: Record<string, unknown> | null;
  cost_usd: number | null;
  from_cache: boolean;
  review_status: "pending" | "approved" | "changes_requested" | "rejected";
  reviewer_notes: string | null;
  reviewed_at: string | null;
  created_at: string;
}

export interface JurisdictionRow {
  country_code: string;
  country_name: string;
  document_type: string | null;
  title: string;
  reference: string;
  summary: string | null;
  source_url: string | null;
  verified: boolean;
}
