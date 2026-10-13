import { cookies, headers } from 'next/headers';
import { LOCALE_COOKIE, isLocale, negotiateLocale, type Locale } from './config';
import { dictionaries, type Dictionary } from './dictionaries';

/** The visitor's chosen language (cookie), otherwise their browser's language. */
export async function getLocale(): Promise<Locale> {
  const cookieLocale = (await cookies()).get(LOCALE_COOKIE)?.value;
  if (isLocale(cookieLocale)) return cookieLocale;
  return negotiateLocale((await headers()).get('accept-language'));
}

export async function getDictionary(): Promise<{ locale: Locale; t: Dictionary }> {
  const locale = await getLocale();
  return { locale, t: dictionaries[locale] };
}
