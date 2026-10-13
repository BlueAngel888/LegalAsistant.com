import {
  arSA, deDE, enUS, esES, frFR, hiIN, idID, itIT, jaJP,
  koKR, nlNL, plPL, ptPT, roRO, ruRU, trTR, ukUA, zhCN,
} from '@clerk/localizations';
import type { Locale } from './config';

/** Translations for Clerk's sign-in / sign-up screens. */
export const clerkLocalizations = {
  ro: roRO, en: enUS, es: esES, fr: frFR, de: deDE, it: itIT, pt: ptPT, pl: plPL, nl: nlNL,
  ru: ruRU, uk: ukUA, tr: trTR, ar: arSA, hi: hiIN, zh: zhCN, ja: jaJP, ko: koKR, id: idID,
} satisfies Record<Locale, unknown>;
