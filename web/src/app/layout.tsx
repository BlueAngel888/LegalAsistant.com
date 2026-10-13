import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "LegalAssistant — analiză AI a documentelor juridice",
  description:
    "Încarcă un contract, o amendă sau o hotărâre și primești o analiză bazată pe legislația țării tale.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <ClerkProvider>
      <html lang="ro">
        <body className="min-h-screen antialiased">
          <Navbar />
          <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
