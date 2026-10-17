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
