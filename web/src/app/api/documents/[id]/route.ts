import { NextResponse } from "next/server";
import { requireUserId } from "@/lib/auth";
import { getDocument, getLatestAnalysis } from "@/lib/db";
import { signedUrl } from "@/lib/storage";
import { jsonError } from "@/utils/http";

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const userId = await requireUserId();
  if (!userId) return jsonError("Unauthorized", 401);
  const { id } = await params;

  const doc = await getDocument(userId, id);
  if (!doc) return jsonError("Document not found.", 404);

  const [previewUrl, analysis] = await Promise.all([
    signedUrl(doc.storage_path),
    getLatestAnalysis(userId, id),
  ]);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { extracted_text, storage_path, ...rest } = doc;
  return NextResponse.json({
    document: { ...rest, text_length: extracted_text?.length ?? 0 },
    previewUrl,
    analysisId: analysis?.id ?? null,
  });
}
