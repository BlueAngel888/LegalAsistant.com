// Central access to environment variables. Throws a clear error at call time
// (not import time) so `next build` works without secrets.
function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing environment variable: ${name}. See .env.example.`);
  }
  return value;
}

export const env = {
  supabaseUrl: () => required("NEXT_PUBLIC_SUPABASE_URL"),
  supabaseServiceRoleKey: () => required("SUPABASE_SERVICE_ROLE_KEY"),
  storageBucket: () => process.env.SUPABASE_STORAGE_BUCKET || "documents",
  anthropicApiKey: () => required("ANTHROPIC_API_KEY"),
  anthropicModel: () => process.env.ANTHROPIC_MODEL || "claude-opus-5-5",
  anthropicEffort: () =>
    (process.env.ANTHROPIC_EFFORT || "high") as
      | "low"
      | "medium"
      | "high"
      | "xhigh"
      | "max",
  maxUploadBytes: () => Number(process.env.MAX_UPLOAD_MB || 4) * 1024 * 1024,
};
