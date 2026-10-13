# LegalAssistant.com — MVP

Upload a legal document (contract, fine, court decision) as PDF and get a structured AI analysis
under the law of the chosen country: summary, strengths, weaknesses, potential errors, defense
strategies, deadlines and legal references. Every analysis is stored with a review status so a
lawyer can verify it later.

**Stack:** Next.js 15 (App Router) · TypeScript · Tailwind CSS 4 · Clerk (auth) · Supabase
(Postgres + Storage) · Claude API (`claude-opus-5-5`) · Vercel.

## Quick start

```bash
cd web
npm install
cp .env.example .env.local     # fill in the keys, see docs/ENVIRONMENT.md
npm run dev                    # http://localhost:3000
```

### 1. Clerk
1. Create an application at <https://dashboard.clerk.com> (Email + Google is enough).
2. Copy the publishable and secret keys into `.env.local`.
3. Production: add your domain under **Domains** and complete the DNS records, otherwise the
   sign-in form stays stuck on loading.

### 2. Supabase
1. Create a project at <https://supabase.com>.
2. **SQL Editor** → run `supabase/migrations/0001_init.sql`, then `0002_seed_jurisdictions.sql`.
   This creates the tables, a private `documents` storage bucket and starter legislation references.
3. Copy the project URL and the **service_role** key into `.env.local`.
   The service role key is used only on the server; never prefix it with `NEXT_PUBLIC_`.

### 3. Anthropic
Create an API key at <https://platform.claude.com> and set `ANTHROPIC_API_KEY`.

### 4. Deploy (Vercel)
Import the repo in Vercel and set **Root Directory = `web`** (the old Flask app stays at the repo root).
Add the environment variables from `docs/ENVIRONMENT.md`, then deploy.
Analysis runs in the background via Next.js `after()` with `maxDuration = 300`, which needs the
Vercel Pro plan for runs over 60 s (Hobby caps functions at 60 s). See *Known limits*.

## Project structure

```
src/
  app/
    page.tsx                     landing
    sign-in/, sign-up/, profile/ Clerk pages
    dashboard/                   documents list
    upload/                      drag-and-drop upload
    documents/[id]/              PDF preview + analysis
    api/
      documents/upload/          POST  upload PDF
      documents/                 GET   list
      documents/[id]/            GET   details + signed preview URL
      analyze/                   POST  start analysis
      analyze/[id]/              GET   status + result
  components/                    Navbar, UploadForm, AnalysisPanel, AnalysisReport, …
  lib/
    claude.ts                    Claude client, prompt caching, structured output
    prompts.ts                   frozen system prompt + jurisdiction block
    analysis-schema.ts           Zod schema of the analysis JSON (+ PROMPT_VERSION)
    analysis-service.ts          result cache → Claude → save
    db.ts, supabase.ts, storage.ts, pdf.ts, auth.ts, env.ts
  utils/                         constants (countries, types, languages), formatting
  middleware.ts                  Clerk route protection
supabase/migrations/             SQL schema + seed
docs/                            API.md, ENVIRONMENT.md
```

## How analysis works and what it costs

1. **Upload:** the PDF goes to Supabase Storage; text is extracted with `unpdf` and saved.
2. **Analyze:** `POST /api/analyze` marks the document `processing`, returns `202`, and runs the
   analysis after the response. The page polls `GET /api/analyze/:id`.
3. **Claude call:** one request to `claude-opus-5-5` with structured output (Zod schema), so the
   result is always valid JSON. Scanned PDFs (no text layer) are sent as PDF so Claude reads the
   page images.

Cost controls, in order of impact:

| Lever | Where | Effect |
|---|---|---|
| Result cache | `analysis-service.ts` | Same file + country + type + language + prompt version reuses the stored analysis. Zero API cost. |
| No accidental re-runs | `POST /api/analyze` | An analysed document is not re-analysed unless `force: true`. |
| Prompt caching | `claude.ts` | System prompt + jurisdiction block are a stable prefix cached for 1 h. It kicks in once that prefix passes the model's minimum cacheable length, so it grows more useful as you add legislation to `jurisdiction_data`. |
| Text instead of PDF | `analysis-service.ts` | Only scans are sent as PDF (more tokens). |
| Cost tracking | `analysis_results.usage`, `cost_usd` | Token usage incl. cache reads/writes per analysis. |

`ANTHROPIC_EFFORT` (default `high`) trades depth for cost; `medium` is cheaper.
Refusal fallback (`fallbacks: "default"`) is enabled, so a rare safety-classifier decline retries
on a fallback model in the same call.

## Preparing for lawyer verification (Week 5)

- `analysis_results.review_status` (`pending` / `approved` / `changes_requested` / `rejected`),
  `reviewer_id`, `reviewer_notes`, `reviewed_at` are ready for a review screen.
- `users.role` supports `analyst` / `admin`.
- `jurisdiction_data.verified` flags legislation references a lawyer has confirmed; unverified
  ones are labelled as such in the prompt.
- `PROMPT_VERSION` and `model` are stored with every analysis, so results stay traceable when
  the prompt changes.

## Known limits (MVP)

- **PDF only, max 4 MB** on Vercel (serverless body limit 4.5 MB). Next step: direct upload to
  Supabase Storage with a signed upload URL, which removes the limit.
- **Background run** uses `after()`; on Vercel Hobby it is cut at 60 s. Use Pro, or move the
  analysis to a Railway worker (the `runAnalysis` function is self-contained for that).
- No payments yet (Stripe is the next step), no admin console, no email notification.

See `docs/API.md` for the endpoints and `docs/ENVIRONMENT.md` for every variable.
