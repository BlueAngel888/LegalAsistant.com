# LegalAssistant.com

Next.js 15 App Router + TypeScript + Tailwind 4, Clerk auth, Supabase (service-role, server only), Claude API.

- Auth: Clerk Core 3 (`@clerk/nextjs` v7). Use `<Show when="signed-in">`, not `SignedIn`/`SignedOut` (removed).
- DB access only through `src/lib/db.ts`; every query filters by the Clerk user id.
- `src/lib/prompts.ts` SYSTEM_PROMPT is frozen for prompt caching: no dates/ids in it. Bump `PROMPT_VERSION` in `analysis-schema.ts` when prompt or schema changes.
- Checks: `npx tsc --noEmit`, `npm run lint`, `npm run build`.
