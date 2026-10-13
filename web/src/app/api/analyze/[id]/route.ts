import { NextResponse } from "next/server";
import { requireUserId } from "@/lib/auth";
import { getDocument, getLatestAnalysis } from "@/lib/db";
import { jsonError } from "@/utils/http";

/** `id` is the document id. Returns status plus the latest analysis when ready. */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const userId = await requireUserId();
  if (!userId) return jsonError("Unauthorized", 401);
  const { id } = await params;

  const doc = await getDocument(userId, id);
  if (!doc) return jsonError("Document not found.", 404);

  const analysis = doc.status === "analyzed" ? await getLatestAnalysis(userId, id) : null;
  return NextResponse.json({
    documentId: id,
    status: doc.status,
    error: doc.error_message,
    analysis: analysis
      ? {
          id: analysis.id,
          result: analysis.result,
          model: analysis.model,
          prompt_version: analysis.prompt_version,
          from_cache: analysis.from_cache,
          review_status: analysis.review_status,
          created_at: analysis.created_at,
        }
      : null,
  });
}
