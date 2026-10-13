# Environment variables

Copy `.env.example` to `.env.local` for local development; set the same keys in Vercel →
Project → Settings → Environment Variables for deployments.

| Variable | Required | Where to find it | Notes |
|---|---|---|---|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | yes | Clerk → API Keys | `pk_test_…` in dev, `pk_live_…` in prod |
| `CLERK_SECRET_KEY` | yes | Clerk → API Keys | server only |
| `NEXT_PUBLIC_CLERK_SIGN_IN_URL` | yes | — | `/sign-in` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_URL` | yes | — | `/sign-up` |
| `NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL` | no | — | `/dashboard` |
| `NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL` | no | — | `/dashboard` |
| `NEXT_PUBLIC_SUPABASE_URL` | yes | Supabase → Project settings → API | |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Supabase → Project settings → API | **server only, bypasses RLS** |
| `SUPABASE_STORAGE_BUCKET` | no | — | default `documents` (created by migration) |
| `ANTHROPIC_API_KEY` | yes | platform.claude.com → API Keys | server only |
| `ANTHROPIC_MODEL` | no | — | default `claude-opus-5-5` |
| `ANTHROPIC_EFFORT` | no | — | `low` / `medium` / `high` (default) / `xhigh` / `max` |
| `MAX_UPLOAD_MB` | no | — | default `4`; keep ≤ 4 on Vercel |

Security notes:
- Only `NEXT_PUBLIC_*` values reach the browser. The Supabase service role key and the
  Anthropic key must never get that prefix.
- `.env*` files are git-ignored (except `.env.example`).
