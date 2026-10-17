#!/usr/bin/env node
// Daily check of the official sources behind the UK niche legal basis.
// Compares each source's live version marker with the reviewed `fingerprint`
// in lib/legal-basis/uk-sources.json and writes a report of what changed.
//
//   node scripts/check-uk-legal-basis.mjs [--markdown report.md] [--json report.json]
//
// Exit code 0: nothing changed. Exit code 1: at least one source changed or
// has no reviewed fingerprint yet. Exit code 2: the check itself failed.

import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const sourcesPath = join(here, '..', 'lib', 'legal-basis', 'uk-sources.json');
const nichesPath = join(here, '..', 'lib', 'legal-basis', 'uk-niches.json');

const args = process.argv.slice(2);
const argValue = (flag) => {
  const i = args.indexOf(flag);
  return i === -1 ? undefined : args[i + 1];
};

async function get(url) {
  const res = await fetch(url, {
    headers: { 'User-Agent': 'legalassistant-legal-basis-check/1.0' },
    redirect: 'follow',
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.text();
}

const hash = (text) => createHash('sha256').update(text).digest('hex').slice(0, 16);

/** legislation.gov.uk: last modification of the revised text plus the number of changes not yet applied. */
async function legislationFingerprint(url) {
  const xml = await get(`${url.replace(/\/$/, '')}/data.xml`);
  const modified = xml.match(/<dc:modified>([^<]+)<\/dc:modified>/)?.[1] ?? 'unknown';
  const unapplied = (xml.match(/<ukm:UnappliedEffect\b/g) ?? []).length;
  return `modified=${modified};unapplied=${unapplied}`;
}

/** GOV.UK: public update date from the Content API. */
async function govukFingerprint(url) {
  const path = new URL(url).pathname;
  const data = JSON.parse(await get(`https://www.gov.uk/api/content${path}`));
  return `updated=${data.public_updated_at ?? data.updated_at ?? 'unknown'}`;
}

/** Any other page: hash of its visible text. */
async function pageFingerprint(url) {
  const html = await get(url);
  const text = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return `text=${hash(text)}`;
}

function fingerprintFor(source) {
  if (source.url.startsWith('https://www.legislation.gov.uk/')) return legislationFingerprint(source.url);
  if (source.url.startsWith('https://www.gov.uk/')) return govukFingerprint(source.url);
  return pageFingerprint(source.url);
}

async function main() {
  const { sources } = JSON.parse(await readFile(sourcesPath, 'utf8'));
  const { niches, globalLimits } = JSON.parse(await readFile(nichesPath, 'utf8'));

  const results = [];
  for (const source of sources) {
    try {
      const live = await fingerprintFor(source);
      results.push({ ...source, live, changed: live !== source.fingerprint });
    } catch (error) {
      results.push({ ...source, live: null, changed: false, error: String(error.message ?? error) });
    }
  }

  const changed = results.filter((r) => r.changed);
  const failed = results.filter((r) => r.error);
  const affected = (id) => [
    ...(globalLimits.some((g) => g.sources.includes(id)) ? ['global limits'] : []),
    ...niches.filter((n) => n.legalBasis.some((b) => b.source === id)).map((n) => n.id),
  ];

  const report = {
    checkedAt: new Date().toISOString(),
    changed: changed.map((r) => ({
      id: r.id,
      title: r.title,
      url: r.url,
      reviewed: r.fingerprint,
      live: r.live,
      niches: affected(r.id),
    })),
    failed: failed.map((r) => ({ id: r.id, url: r.url, error: r.error })),
  };

  const md = [
    `Checked ${results.length} official sources on ${report.checkedAt.slice(0, 10)}.`,
    '',
    changed.length
      ? '| Source | Reviewed | Live | Niches |\n|---|---|---|---|\n' +
        report.changed
          .map((c) => `| [${c.title}](${c.url}) \`${c.id}\` | \`${c.reviewed ?? 'none'}\` | \`${c.live}\` | ${c.niches.join(', ') || 'none'} |`)
          .join('\n')
      : 'No source changed.',
    '',
    failed.length ? `Could not check: ${report.failed.map((f) => `\`${f.id}\` (${f.error})`).join(', ')}` : '',
  ].join('\n');

  const mdPath = argValue('--markdown');
  const jsonPath = argValue('--json');
  if (mdPath) await writeFile(mdPath, md);
  if (jsonPath) await writeFile(jsonPath, JSON.stringify(report, null, 2));
  console.log(md);

  if (failed.length === results.length) process.exit(2);
  process.exit(changed.length ? 1 : 0);
}

main().catch((error) => {
  console.error(error);
  process.exit(2);
});
