import { NextResponse } from "next/server";
import { createHash, randomUUID } from "node:crypto";
import { requireUserId } from "@/lib/auth";
import { supabaseAdmin } from "@/lib/supabase";
import { uploadFile, removeFile } from "@/lib/storage";
import { isPdf, parsePdf } from "@/lib/pdf";
import { env } from "@/lib/env";
import { jsonError } from "@/utils/http";
import { COUNTRIES, DOCUMENT_TYPES, LANGUAGES } from "@/utils/constants";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: Request) {
  const userId = await requireUserId();
  if (!userId) return jsonError("Unauthorized", 401);

  const form = await req.formData().catch(() => null);
  const file = form?.get("file");
  if (!(file instanceof File)) return jsonError("Missing file field 'file'.");

  const countryCode = String(form?.get("country") ?? "RO").toUpperCase();
  const documentType = String(form?.get("documentType") ?? "other");
  const language = String(form?.get("language") ?? "ro");
  if (!COUNTRIES.some((c) => c.code === countryCode)) return jsonError("Unsupported country.");
  if (!DOCUMENT_TYPES.some((d) => d.value === documentType)) return jsonError("Unsupported document type.");
  if (!LANGUAGES.some((l) => l.code === language)) return jsonError("Unsupported language.");

  if (file.size > env.maxUploadBytes()) {
    return jsonError(`File too large. Maximum is ${process.env.MAX_UPLOAD_MB || 4} MB.`, 413);
  }

  const bytes = new Uint8Array(await file.arrayBuffer());
  if (!isPdf(bytes)) return jsonError("Only PDF files are supported for now.", 415);

  let text = "";
  let pageCount: number | null = null;
  try {
    const parsed = await parsePdf(bytes);
    text = parsed.text;
    pageCount = parsed.pageCount;
  } catch {
    return jsonError("Could not read this PDF. It may be corrupted or password-protected.", 422);
  }

  const id = randomUUID();
  const storagePath = `${userId}/${id}.pdf`;
  const fileHash = createHash("sha256").update(bytes).digest("hex");

  await uploadFile(storagePath, bytes, "application/pdf");

  const { data, error } = await supabaseAdmin()
    .from("documents")
    .insert({
      id,
      user_id: userId,
      file_name: file.name.slice(0, 255),
      storage_path: storagePath,
      mime_type: "application/pdf",
      size_bytes: file.size,
      page_count: pageCount,
      extracted_text: text,
      text_hash: fileHash,
      country_code: countryCode,
      document_type: documentType,
      language,
      status: "uploaded",
    })
    .select("id, file_name, status, page_count, created_at")
    .single();

  if (error) {
    await removeFile(storagePath);
    return jsonError(`Could not save document: ${error.message}`, 500);
  }

  return NextResponse.json({ document: data, scanned: text.length < 200 }, { status: 201 });
}
