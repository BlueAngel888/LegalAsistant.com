export const COUNTRIES = [
  { code: "RO", name: "România" },
  { code: "MD", name: "Moldova" },
  { code: "DE", name: "Deutschland" },
  { code: "GB", name: "United Kingdom" },
  { code: "FR", name: "France" },
  { code: "IT", name: "Italia" },
  { code: "ES", name: "España" },
  { code: "AT", name: "Österreich" },
  { code: "NL", name: "Nederland" },
  { code: "US", name: "United States" },
] as const;

export const DOCUMENT_TYPES = [
  { value: "contract", label: "Contract" },
  { value: "fine", label: "Amendă / proces-verbal" },
  { value: "court_decision", label: "Hotărâre judecătorească" },
  { value: "other", label: "Alt document" },
] as const;

export const LANGUAGES = [
  { code: "ro", name: "Română" },
  { code: "en", name: "English" },
  { code: "de", name: "Deutsch" },
  { code: "fr", name: "Français" },
  { code: "it", name: "Italiano" },
  { code: "es", name: "Español" },
] as const;

export type CountryCode = (typeof COUNTRIES)[number]["code"];
export type DocumentType = (typeof DOCUMENT_TYPES)[number]["value"];
export type LanguageCode = (typeof LANGUAGES)[number]["code"];

export const countryName = (code: string) =>
  COUNTRIES.find((c) => c.code === code)?.name ?? code;
export const documentTypeLabel = (value: string) =>
  DOCUMENT_TYPES.find((d) => d.value === value)?.label ?? value;
export const languageName = (code: string) =>
  LANGUAGES.find((l) => l.code === code)?.name ?? code;
