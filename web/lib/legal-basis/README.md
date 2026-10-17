# UK legal basis per niche

- `uk-niches.json`: for each niche, whether it can be offered in England and Wales, its limits and the provisions it rests on.
- `uk-sources.json`: the official sources those provisions come from, with the version each extract was reviewed against (`fingerprint`).
- `uk.ts`: typed access, and `ukLegalBasisPrompt(nicheId)` to give an analysis the checked legal basis.

## Daily update

1. `.github/workflows/uk-legal-basis-check.yml` runs every morning and calls `scripts/check-uk-legal-basis.mjs`. When a source differs from its reviewed version, it keeps one open issue labelled `legal-basis-uk` with the list of changes and the niches they affect.
2. A daily Claude task reads that issue, rereads each changed source, updates the affected extracts, sets `fingerprint` to the live value from the issue and `verifiedAt` to the day, and opens a pull request.
3. Once the pull request is merged, the next check finds no difference and closes the issue.

A change to a source in the global limits (Legal Services Act 2007, FCA claims management or debt counselling) is flagged in the pull request, since it can change which niches may be offered at all.

The list is not confirmed by a UK lawyer.
