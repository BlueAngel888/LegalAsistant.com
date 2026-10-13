import type { Metadata } from 'next';
import { ClerkProvider } from '@clerk/nextjs';
import './globals.css';

export const metadata: Metadata = {
  title: 'Legal Assistant - AI-Powered Document Analysis',
  description: 'Analyze legal documents with AI-powered insights using Claude',
  keywords: ['legal', 'document', 'analysis', 'AI', 'contracts', 'law'],
  authors: [{ name: 'Legal Assistant Team' }],
  openGraph: {
    title: 'Legal Assistant',
    description: 'Analyze legal documents with AI-powered insights',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <head>
          <meta charSet="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1" />
          <meta name="theme-color" content="#05060f" />
        </head>
        <body className="antialiased">
          <div className="min-h-screen">
            {children}
          </div>
        </body>
      </html>
    </ClerkProvider>
  );
}
