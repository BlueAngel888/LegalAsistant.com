import type { Metadata } from 'next';
import { ClerkProvider } from '@clerk/nextjs';
import { I18nProvider } from '@/app/components/I18nProvider';
import { clerkLocalizations } from '@/lib/i18n/clerk';
import { localeInfo, locales } from '@/lib/i18n/config';
import { getDictionary } from '@/lib/i18n/server';
import './globals.css';

export async function generateMetadata(): Promise<Metadata> {
  const { locale, t } = await getDictionary();
  return {
    title: t.meta.title,
    description: t.meta.description,
    keywords: ['legal', 'document', 'analysis', 'AI', 'contracts', 'law'],
    authors: [{ name: 'Legal Assistant Team' }],
    openGraph: {
      title: 'Legal Assistant',
      description: t.meta.description,
      type: 'website',
      locale: localeInfo[locale].tag.replace('-', '_'),
      alternateLocale: locales.filter((l) => l !== locale).map((l) => localeInfo[l].tag.replace('-', '_')),
    },
  };
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { locale, t } = await getDictionary();
  const { tag, dir } = localeInfo[locale];

  return (
    <ClerkProvider
      localization={clerkLocalizations[locale]}
      signInFallbackRedirectUrl="/dashboard"
      signUpFallbackRedirectUrl="/dashboard"
    >
      <html lang={tag} dir={dir} suppressHydrationWarning>
        <head>
          <meta charSet="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <meta name="theme-color" content="#05060f" />
        </head>
        <body className="antialiased">
          <I18nProvider locale={locale} t={t}>
            <div className="min-h-screen">
              {children}
            </div>
          </I18nProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
