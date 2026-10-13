export const locales = [
  'ro',
  'en',
  'es',
  'fr',
  'de',
  'it',
  'pt',
  'pl',
  'nl',
  'ru',
  'uk',
  'tr',
  'ar',
  'hi',
  'zh',
  'ja',
  'ko',
  'id',
] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'en';

export const LOCALE_COOKIE = 'NEXT_LOCALE';

interface LocaleInfo {
  /** Name of the language written in that language, shown in the switcher. */
  nativeName: string;
  /** English name, used to instruct Claude which language to answer in. */
  englishName: string;
  /** BCP 47 tag used for dates and the <html lang> attribute. */
  tag: string;
  dir: 'ltr' | 'rtl';
  flag: string;
}

export const localeInfo: Record<Locale, LocaleInfo> = {
  ro: { nativeName: 'Română', englishName: 'Romanian', tag: 'ro-RO', dir: 'ltr', flag: '🇷🇴' },
  en: { nativeName: 'English', englishName: 'English', tag: 'en-US', dir: 'ltr', flag: '🇬🇧' },
  es: { nativeName: 'Español', englishName: 'Spanish', tag: 'es-ES', dir: 'ltr', flag: '🇪🇸' },
  fr: { nativeName: 'Français', englishName: 'French', tag: 'fr-FR', dir: 'ltr', flag: '🇫🇷' },
  de: { nativeName: 'Deutsch', englishName: 'German', tag: 'de-DE', dir: 'ltr', flag: '🇩🇪' },
  it: { nativeName: 'Italiano', englishName: 'Italian', tag: 'it-IT', dir: 'ltr', flag: '🇮🇹' },
  pt: { nativeName: 'Português', englishName: 'Portuguese', tag: 'pt-PT', dir: 'ltr', flag: '🇵🇹' },
  pl: { nativeName: 'Polski', englishName: 'Polish', tag: 'pl-PL', dir: 'ltr', flag: '🇵🇱' },
  nl: { nativeName: 'Nederlands', englishName: 'Dutch', tag: 'nl-NL', dir: 'ltr', flag: '🇳🇱' },
  ru: { nativeName: 'Русский', englishName: 'Russian', tag: 'ru-RU', dir: 'ltr', flag: '🇷🇺' },
  uk: { nativeName: 'Українська', englishName: 'Ukrainian', tag: 'uk-UA', dir: 'ltr', flag: '🇺🇦' },
  tr: { nativeName: 'Türkçe', englishName: 'Turkish', tag: 'tr-TR', dir: 'ltr', flag: '🇹🇷' },
  ar: { nativeName: 'العربية', englishName: 'Arabic', tag: 'ar', dir: 'rtl', flag: '🇸🇦' },
  hi: { nativeName: 'हिन्दी', englishName: 'Hindi', tag: 'hi-IN', dir: 'ltr', flag: '🇮🇳' },
  zh: { nativeName: '简体中文', englishName: 'Simplified Chinese', tag: 'zh-CN', dir: 'ltr', flag: '🇨🇳' },
  ja: { nativeName: '日本語', englishName: 'Japanese', tag: 'ja-JP', dir: 'ltr', flag: '🇯🇵' },
  ko: { nativeName: '한국어', englishName: 'Korean', tag: 'ko-KR', dir: 'ltr', flag: '🇰🇷' },
  id: { nativeName: 'Bahasa Indonesia', englishName: 'Indonesian', tag: 'id-ID', dir: 'ltr', flag: '🇮🇩' },
};

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (locales as readonly string[]).includes(value);
}

/** Maps a tag such as "pt-BR" or "zh-Hans-CN" to a supported locale, if any. */
export function matchLocale(tag: string | undefined | null): Locale | undefined {
  if (!tag) return undefined;
  const base = tag.trim().toLowerCase().split(/[-_]/)[0];
  return isLocale(base) ? base : undefined;
}

/** Picks the best supported locale from an Accept-Language header. */
export function negotiateLocale(acceptLanguage: string | null | undefined): Locale {
  if (!acceptLanguage) return defaultLocale;

  const ranked = acceptLanguage
    .split(',')
    .map((part) => {
      const [tag, ...params] = part.trim().split(';');
      const q = params.find((p) => p.trim().startsWith('q='));
      return { tag, q: q ? parseFloat(q.trim().slice(2)) || 0 : 1 };
    })
    .filter(({ q }) => q > 0)
    .sort((a, b) => b.q - a.q);

  for (const { tag } of ranked) {
    const match = matchLocale(tag);
    if (match) return match;
  }
  return defaultLocale;
}
