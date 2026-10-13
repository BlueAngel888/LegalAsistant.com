import "server-only";
import { supabaseAdmin } from "./supabase";
import { env } from "./env";

export async function uploadFile(path: string, bytes: Uint8Array, contentType: string) {
  const { error } = await supabaseAdmin()
    .storage.from(env.storageBucket())
    .upload(path, bytes, { contentType, upsert: false });
  if (error) throw new Error(`Storage upload failed: ${error.message}`);
}

export async function downloadFile(path: string): Promise<Uint8Array> {
  const { data, error } = await supabaseAdmin()
    .storage.from(env.storageBucket())
    .download(path);
  if (error || !data) throw new Error(`Storage download failed: ${error?.message}`);
  return new Uint8Array(await data.arrayBuffer());
}

export async function removeFile(path: string) {
  await supabaseAdmin().storage.from(env.storageBucket()).remove([path]);
}

/** Short-lived URL for previewing the PDF in the browser. */
export async function signedUrl(path: string, expiresInSeconds = 600): Promise<string> {
  const { data, error } = await supabaseAdmin()
    .storage.from(env.storageBucket())
    .createSignedUrl(path, expiresInSeconds);
  if (error || !data) throw new Error(`Signed URL failed: ${error?.message}`);
  return data.signedUrl;
}
