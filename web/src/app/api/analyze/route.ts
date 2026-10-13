import { NextResponse, after } from "next/server";
import { requireUserId } from "@/lib/auth";
import { getDocument, updateDocument } from "@/lib/db";
import { runAnalysis } from "@/lib/analysis-service";
import { jsonError } from "@/utils/http";

export const runtime = "nodejs";
// The analysis runs after the response is sent (see `after` below); this is
// how long the function may stay alive to finish it.
export const maxDuration = 300;

export async function POST(req: Request) {
  const userId = await requireUserId();
  if (!userId) return jsonError("Unauthorized", 401);

  const body = await req.json().catch(() => ({}));
  const documentId = typeof body?.documentId === "string" ? body.documentId : null;
  const force = body?.force === true;
  if (!documentId) return jsonError("Missing documentId.");

  const doc = await getDocument(userId, documentId);
  if (!doc) return jsonError("Document not found.", 404);

  // A run that has been "processing" for over 10 minutes is treated as dead.
  const stale = Date.now() - new Date(doc.updated_at).getTime() > 10 * 60 * 1000;
  if (doc.status === "processing" && !stale) {
    return NextResponse.json({ documentId, status: "processing" }, { status: 202 });
  }
  // Already analysed: don't spend another API call unless explicitly asked.
  if (doc.status === "analyzed" && !force) {
    return NextResponse.json({ documentId, status: "analyzed" });
  }

  await updateDocument(doc.id, { status: "processing", error_message: null });
  after(() => runAnalysis({ ...doc, status: "processing" }, { skipResultCache: force }));

  return NextResponse.json({ documentId, status: "processing" }, { status: 202 });
}
