import { SignUpButton, SignInButton, SignedIn, SignedOut, UserButton } from '@clerk/nextjs';
import Link from 'next/link';
import {
  ArrowRight,
  Shield,
  Zap,
  FileText,
  Globe2,
  Scale,
  AlertTriangle,
  Target,
  Gauge,
  Languages,
  ScanSearch,
  Sparkles,
  Lock,
  Mail,
} from 'lucide-react';
import { LanguageSwitcher } from '@/app/components/LanguageSwitcher';
import { getDictionary } from '@/lib/i18n/server';
import { CONTACT_EMAIL } from '@/lib/site';

export default async function HomePage() {
  const { t } = await getDictionary();

  const features = [
    { icon: Zap, title: t.features.instantTitle, desc: t.features.instantDesc },
    { icon: Lock, title: t.features.secureTitle, desc: t.features.secureDesc },
    { icon: Globe2, title: t.features.jurisdictionsTitle, desc: t.features.jurisdictionsDesc },
    { icon: FileText, title: t.features.formatTitle, desc: t.features.formatDesc },
  ];

  const outputs = [
    { icon: ScanSearch, title: t.outputs.jurisdictionTitle, desc: t.outputs.jurisdictionDesc },
    { icon: Scale, title: t.outputs.strengthsTitle, desc: t.outputs.strengthsDesc },
    { icon: AlertTriangle, title: t.outputs.errorsTitle, desc: t.outputs.errorsDesc },
    { icon: Target, title: t.outputs.strategyTitle, desc: t.outputs.strategyDesc },
    { icon: Gauge, title: t.outputs.riskTitle, desc: t.outputs.riskDesc },
    { icon: Languages, title: t.outputs.languagesTitle, desc: t.outputs.languagesDesc },
  ];

  const riskRows = [
    { label: t.mock.termination, level: t.risk.HIGH, width: 'w-4/5', color: 'from-red-400 to-orange-400', text: 'text-red-300' },
    { label: t.mock.liability, level: t.risk.MEDIUM, width: 'w-1/2', color: 'from-amber-300 to-yellow-400', text: 'text-amber-300' },
    { label: t.mock.governingLaw, level: t.risk.LOW, width: 'w-1/4', color: 'from-emerald-300 to-cyan-400', text: 'text-emerald-300' },
  ];

  const footerColumns = [
    { title: t.footer.product, links: [t.footer.features, t.footer.pricing, t.footer.documentation] },
    { title: t.footer.company, links: [t.footer.about, t.footer.blog, t.footer.contact] },
    { title: t.footer.legal, links: [t.footer.privacy, t.footer.terms, t.footer.security] },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 grid-bg" aria-hidden />

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/60 backdrop-blur-xl">
        <nav className="container py-4 flex justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-7 h-7 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.7)]" />
            <span className="text-xl font-semibold tracking-tight text-white">
              Legal<span className="text-gradient">Assistant</span>
            </span>
          </div>
          <div className="flex gap-2 sm:gap-3">
            <LanguageSwitcher />
            <SignedOut>
              <SignInButton mode="modal">
                <button className="btn btn-secondary hidden sm:inline-flex">{t.nav.signIn}</button>
              </SignInButton>
              <SignUpButton mode="modal">
                <button className="btn btn-primary">{t.nav.getStarted}</button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn btn-primary hover:text-slate-950">{t.dashboard.openApp}</Link>
              <div className="flex items-center"><UserButton /></div>
            </SignedIn>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative container pt-16 pb-24 sm:pt-24">
        <div className="grid lg:grid-cols-2 gap-14 items-center">
          <div>
            <span className="badge-primary gap-1.5 mb-6">
              <Sparkles className="w-3.5 h-3.5" /> {t.hero.badge}
            </span>
            <h1 className="text-4xl sm:text-6xl font-bold leading-[1.05] mb-6">
              {t.hero.titleStart}{' '}
              <span className="text-gradient">{t.hero.titleHighlight}</span>
            </h1>
            <p className="text-lg sm:text-xl text-slate-400 mb-10 max-w-xl">
              {t.hero.subtitle}
            </p>
            <div className="flex flex-wrap gap-4">
              <SignedOut>
                <SignUpButton mode="modal">
                  <button className="btn btn-primary btn-large">
                    {t.hero.cta} <ArrowRight className="w-5 h-5 rtl:rotate-180" />
                  </button>
                </SignUpButton>
              </SignedOut>
              <SignedIn>
                <Link href="/dashboard" className="btn btn-primary btn-large hover:text-slate-950">
                  {t.hero.cta} <ArrowRight className="w-5 h-5 rtl:rotate-180" />
                </Link>
              </SignedIn>
              <a href="#features" className="btn btn-secondary btn-large hover:text-white">
                {t.hero.learnMore}
              </a>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-8 gap-y-3 text-sm text-slate-400">
              <span className="flex items-center gap-2"><Lock className="w-4 h-4 text-cyan-400" /> {t.hero.trustEncrypted}</span>
              <span className="flex items-center gap-2"><Globe2 className="w-4 h-4 text-cyan-400" /> {t.hero.trustLaw}</span>
              <span className="flex items-center gap-2"><Zap className="w-4 h-4 text-cyan-400" /> {t.hero.trustFast}</span>
            </div>
          </div>

          {/* Hero visual: mock analysis panel */}
          <div className="relative animate-float">
            <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-tr from-cyan-500/20 via-sky-500/10 to-violet-500/25 blur-3xl" aria-hidden />
            <div className="relative card glow p-6 sm:p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-cyan-300" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">Service_Agreement.pdf</p>
                    <p className="text-xs text-slate-500">{t.mock.fileMeta}</p>
                  </div>
                </div>
                <span className="badge-success">{t.mock.analyzed}</span>
              </div>

              <div className="relative h-36 rounded-xl border border-white/10 bg-slate-950/60 overflow-hidden mb-6 p-4 space-y-2.5">
                <div className="scan-line" aria-hidden />
                {['w-11/12', 'w-4/5', 'w-full', 'w-3/4', 'w-5/6', 'w-2/3'].map((w, i) => (
                  <div key={i} className={`h-2 rounded-full bg-white/10 ${w}`} />
                ))}
              </div>

              <div className="space-y-4">
                {riskRows.map((r) => (
                  <div key={r.label}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-slate-300">{r.label}</span>
                      <span className={r.text}>{r.level}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-white/5">
                      <div className={`h-1.5 rounded-full bg-gradient-to-r ${r.color} ${r.width}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative py-24 border-t border-white/5">
        <div className="container">
          <div className="text-center mb-14">
            <p className="text-sm uppercase tracking-[0.2em] text-cyan-400 mb-3">{t.features.eyebrow}</p>
            <h2 className="text-3xl sm:text-4xl font-bold">{t.features.title}</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="group card p-6 transition duration-300 hover:-translate-y-1 hover:border-cyan-400/40"
              >
                <div className="mb-5 w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br from-cyan-400/20 to-violet-400/20 border border-white/10 group-hover:shadow-[0_0_24px_rgba(34,211,238,0.35)] transition">
                  <Icon className="w-6 h-6 text-cyan-300" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* What you get */}
      <section className="relative container py-24">
        <div className="text-center mb-14">
          <p className="text-sm uppercase tracking-[0.2em] text-violet-400 mb-3">{t.outputs.eyebrow}</p>
          <h2 className="text-3xl sm:text-4xl font-bold">{t.outputs.title}</h2>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {outputs.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card p-6 flex gap-4 transition hover:border-violet-400/40">
              <Icon className="w-6 h-6 shrink-0 text-violet-300 mt-0.5" />
              <div>
                <h3 className="text-lg font-semibold mb-1">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative container pb-24">
        <div className="relative card glow overflow-hidden px-6 py-16 text-center">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/15 via-transparent to-violet-500/20" aria-hidden />
          <div className="relative">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              {t.cta.titleStart} <span className="text-gradient">{t.cta.titleHighlight}</span>
            </h2>
            <p className="text-lg text-slate-400 mb-8">{t.cta.subtitle}</p>
            <SignedOut>
              <SignUpButton mode="modal">
                <button className="btn btn-primary btn-large">
                  {t.cta.button} <ArrowRight className="w-5 h-5 rtl:rotate-180" />
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn btn-primary btn-large hover:text-slate-950">
                {t.dashboard.openApp} <ArrowRight className="w-5 h-5 rtl:rotate-180" />
              </Link>
            </SignedIn>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-white/10 py-12 text-slate-400">
        <div className="container">
          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-8 mb-10">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-cyan-400" />
                <span className="font-semibold text-white">LegalAssistant</span>
              </div>
              <p className="text-sm">{t.footer.tagline}</p>
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="mt-4 inline-flex items-center gap-2 text-sm text-cyan-300 hover:text-white"
              >
                <Mail className="w-4 h-4" />
                {CONTACT_EMAIL}
              </a>
            </div>
            {footerColumns.map((col) => (
              <div key={col.title}>
                <h4 className="text-sm font-semibold text-white mb-4">{col.title}</h4>
                <ul className="text-sm space-y-2">
                  {col.links.map((l) => (
                    <li key={l}>
                      <a href={l === t.footer.contact ? `mailto:${CONTACT_EMAIL}` : '#'} className="text-slate-400 hover:text-white">{l}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-sm">
            <p>&copy; {new Date().getFullYear()} LegalAssistant. {t.footer.rights}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
