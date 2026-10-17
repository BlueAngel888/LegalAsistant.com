import type { AnalysisPoint, ComplianceStatus, PublicInfoItem } from './types';

const STATUSES: ComplianceStatus[] = ['COMPLIANT', 'NON_COMPLIANT', 'UNCLEAR'];

/**
 * Turns whatever Claude or the database returned into analysis points.
 * Plain strings (older analyses) become points without a legal basis.
 */
export function toAnalysisPoints(value: unknown): AnalysisPoint[] {
  if (!Array.isArray(value)) return [];

  return value.flatMap((item): AnalysisPoint[] => {
    if (typeof item === 'string') {
      return item.trim() ? [{ text: item, legalBasis: '' }] : [];
    }
    if (!item || typeof item !== 'object' || typeof item.text !== 'string' || !item.text.trim()) {
      return [];
    }
    const status = STATUSES.includes(item.status) ? (item.status as ComplianceStatus) : undefined;
    return [
      {
        text: item.text,
        legalBasis: typeof item.legalBasis === 'string' ? item.legalBasis : '',
        ...(status && { status }),
      },
    ];
  });
}

export function toStringList(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === 'string' && item.trim() !== '');
}

export function toPublicInfo(value: unknown): PublicInfoItem[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item): PublicInfoItem[] => {
    if (!item || typeof item !== 'object' || typeof item.text !== 'string' || !item.text.trim()) {
      return [];
    }
    return [{ text: item.text, source: typeof item.source === 'string' ? item.source : '' }];
  });
}
