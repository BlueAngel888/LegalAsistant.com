# API

All endpoints require a signed-in Clerk session (cookie). Unauthenticated calls get `401`
(or a redirect to `/sign-in`, enforced by `src/middleware.ts`). Errors are `{ "error": string }`.
Users can only see their own documents; any other id returns `404`.

## POST /api/documents/upload
`multipart/form-data`

| Field | Type | Default | Allowed |
|---|---|---|---|
| `file` | PDF file | — | `%PDF` files up to `MAX_UPLOAD_MB` |
| `country` | string | `RO` | see `src/utils/constants.ts` |
| `documentType` | string | `other` | `contract`, `fine`, `court_decision`, `other` |
| `language` | string | `ro` | `ro`, `en`, `de`, `fr`, `it`, `es` |

`201` → `{ "document": { "id", "file_name", "status", "page_count", "created_at" }, "scanned": boolean }`
Errors: `400` bad field, `413` too large, `415` not a PDF, `422` unreadable PDF.

## GET /api/documents
`200` → `{ "documents": DocumentSummary[] }`, newest first. No extracted text or storage paths.

## GET /api/documents/:id
`200` → `{ "document": {…, "text_length"}, "previewUrl": string, "analysisId": string | null }`
`previewUrl` is a signed Supabase Storage URL valid for 10 minutes.

## POST /api/analyze
JSON body: `{ "documentId": string, "force"?: boolean }`

- `202 { "status": "processing" }` — analysis started (or already running).
- `200 { "status": "analyzed" }` — already analysed; nothing is spent. Send `force: true` to
  re-run and bypass the result cache.

The analysis runs after the response; poll `GET /api/analyze/:id`.

## GET /api/analyze/:id
`:id` is the **document** id.

```json
{
  "documentId": "…",
  "status": "uploaded | processing | analyzed | failed",
  "error": null,
  "analysis": {
    "id": "…",
    "model": "claude-opus-5-5",
    "prompt_version": "2026-10-12.v1",
    "from_cache": false,
    "review_status": "pending",
    "created_at": "…",
    "result": {
      "summary": "…",
      "document_type_detected": "…",
      "jurisdiction": "…",
      "parties": [{ "name": "…", "role": "…" }],
      "key_dates": [{ "date": "…", "description": "…" }],
      "strengths": [{ "title": "…", "explanation": "…", "legal_basis": "…" }],
      "weaknesses": [ … ],
      "potential_errors": [{ "title": "…", "explanation": "…", "legal_basis": "…", "severity": "low|medium|high" }],
      "defense_strategies": [{ "title": "…", "steps": ["…"], "legal_basis": "…", "likelihood_of_success": "low|medium|high" }],
      "deadlines_and_actions": [{ "action": "…", "deadline": "…", "urgency": "low|medium|high" }],
      "legal_references": [{ "reference": "…", "relevance": "…" }],
      "risk_level": "low|medium|high",
      "confidence": "low|medium|high",
      "missing_information": ["…"],
      "disclaimer": "…"
    }
  }
}
```
The schema source of truth is `src/lib/analysis-schema.ts`.
