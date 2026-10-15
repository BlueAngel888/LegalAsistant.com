/** Price of one document analysis, in cents. Safe to import on the client. */
export const ANALYSIS_PRICE_CENTS = 9900;
export const ANALYSIS_CURRENCY = 'eur';

/** The analysis price written for the given BCP 47 locale tag, e.g. "99,00 €". */
export function formatAnalysisPrice(localeTag: string): string {
  return new Intl.NumberFormat(localeTag, {
    style: 'currency',
    currency: ANALYSIS_CURRENCY.toUpperCase(),
    minimumFractionDigits: 0,
  }).format(ANALYSIS_PRICE_CENTS / 100);
}
