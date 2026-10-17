import niches from './uk-niches.json';
import sources from './uk-sources.json';

/** Whether a niche may be offered in England and Wales. */
export type NicheStatus = 'allowed' | 'allowed_with_limits' | 'postponed' | 'excluded';

export interface LegalSource {
  id: string;
  title: string;
  kind: 'legislation' | 'govuk' | 'fca' | 'guidance' | 'case';
  url: string;
  /** Version marker of the source when the extracts were last reviewed. */
  fingerprint: string | null;
}

export interface LegalBasisEntry {
  provision: string;
  source: string;
  point: string;
}

export interface UkNiche {
  id: string;
  nameRo: string;
  status: NicheStatus;
  scope: string;
  limits: string[];
  legalBasis: LegalBasisEntry[];
}

export const ukSources = sources.sources as LegalSource[];
export const ukNiches = niches.niches as UkNiche[];
export const ukGlobalLimits = niches.globalLimits;
export const ukLegalBasisVerifiedAt = niches.verifiedAt;

const sourceById = new Map(ukSources.map((s) => [s.id, s]));

export function getUkNiche(id: string): UkNiche | undefined {
  return ukNiches.find((n) => n.id === id);
}

/** Niches that can be sold now (allowed, or allowed within their limits). */
export function offerableUkNiches(): UkNiche[] {
  return ukNiches.filter((n) => n.status === 'allowed' || n.status === 'allowed_with_limits');
}

/** True when the niche may be analysed (fully or within its limits). */
export function isOfferableUkNiche(id: string | null | undefined): boolean {
  const niche = id ? getUkNiche(id) : undefined;
  return niche?.status === 'allowed' || niche?.status === 'allowed_with_limits';
}

/** The niche's own limits plus the limits that apply to every UK service. */
export function ukLimitsFor(id: string): string[] {
  const niche = getUkNiche(id);
  return [...(niche?.limits ?? []), ...ukGlobalLimits.map((g) => g.rule)];
}

/** Official sources cited by a niche's legal basis, in order and without duplicates. */
export function ukSourcesFor(id: string): LegalSource[] {
  const ids = new Set(getUkNiche(id)?.legalBasis.map((b) => b.source) ?? []);
  return [...ids].flatMap((sid) => sourceById.get(sid) ?? []);
}

/**
 * The whole UK catalogue as prompt text: which niches may be analysed, the
 * scope and limits of each, and the checked legal basis to cite.
 */
export function ukCatalogPrompt(): string {
  const entry = (e: LegalBasisEntry) => {
    const src = sourceById.get(e.source);
    return `    - ${e.provision}: ${e.point}${src ? ` (${src.url})` : ''}`;
  };
  const offered = offerableUkNiches().map((n) =>
    [
      `- id "${n.id}" (${n.status === 'allowed' ? 'allowed' : 'allowed with limits'})`,
      `  Scope: ${n.scope}`,
      ...(n.limits.length ? ['  Limits:', ...n.limits.map((l) => `    - ${l}`)] : []),
      '  Legal basis:',
      ...n.legalBasis.map(entry),
    ].join('\n'),
  );
  const notOffered = ukNiches
    .filter((n) => !isOfferableUkNiche(n.id))
    .map((n) => `- ${n.id}: ${n.scope} ${n.limits.join(' ')}`);

  return [
    `UK SERVICE CATALOGUE (${niches.jurisdiction}; legal basis verified against official sources on ${ukLegalBasisVerifiedAt}).`,
    'Limits that apply to every UK analysis:',
    ...ukGlobalLimits.map((g) => `- ${g.rule}`),
    'Niches that may be analysed:',
    ...offered,
    'Niches that are not offered:',
    ...notOffered,
  ].join('\n');
}

/**
 * The legal basis of a niche as prompt text, so an analysis cites the
 * provisions already checked against the official sources.
 */
export function ukLegalBasisPrompt(id: string): string {
  const niche = getUkNiche(id);
  if (!niche || niche.status === 'postponed' || niche.status === 'excluded') return '';

  const line = (e: LegalBasisEntry) => {
    const src = sourceById.get(e.source);
    return `- ${e.provision}: ${e.point}${src ? ` (${src.url})` : ''}`;
  };

  return [
    `Jurisdiction: ${niches.jurisdiction}. Legal basis verified against official sources on ${ukLegalBasisVerifiedAt}; apply the law in force on the analysis date.`,
    `Scope: ${niche.scope}`,
    'Legal basis:',
    ...niche.legalBasis.map(line),
    'Limits for this service:',
    ...niche.limits.map((l) => `- ${l}`),
    ...ukGlobalLimits.map((g) => `- ${g.rule}`),
  ].join('\n');
}
