'use client';

import { useEffect, useRef, useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { Check, ChevronDown, Globe } from 'lucide-react';
import { LOCALE_COOKIE, localeInfo, locales, type Locale } from '@/lib/i18n/config';
import { useI18n } from './I18nProvider';

export function LanguageSwitcher() {
  const { locale, t } = useI18n();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('pointerdown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const choose = (next: Locale) => {
    setOpen(false);
    if (next === locale) return;
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    startTransition(() => router.refresh());
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={t.nav.language}
        className={`btn btn-secondary ${pending ? 'opacity-60' : ''}`}
      >
        <Globe className="w-4 h-4 text-cyan-300" />
        <span className="hidden sm:inline">{localeInfo[locale].nativeName}</span>
        <span className="sm:hidden uppercase">{locale}</span>
        <ChevronDown className={`w-3.5 h-3.5 transition ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label={t.nav.language}
          className="absolute end-0 mt-2 w-56 max-h-[70vh] overflow-y-auto rounded-xl border border-white/10 bg-slate-950/95 backdrop-blur-xl p-1.5 shadow-[0_20px_50px_-20px_rgba(0,0,0,0.8)] z-50"
        >
          {locales.map((code) => {
            const info = localeInfo[code];
            const active = code === locale;
            return (
              <li key={code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={active}
                  lang={info.tag}
                  dir={info.dir}
                  onClick={() => choose(code)}
                  className={`w-full flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-start transition ${
                    active ? 'bg-cyan-400/10 text-cyan-200' : 'text-slate-300 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <span aria-hidden>{info.flag}</span>
                  <span className="flex-1">{info.nativeName}</span>
                  {active && <Check className="w-4 h-4" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
