'use client';

import { useEffect, useRef, useState } from 'react';
import { CreditCard, Loader2 } from 'lucide-react';
import { Header } from '@/app/components/Header';
import { DocumentUpload } from '@/app/components/DocumentUpload';
import { AnalysisResultComponent } from '@/app/components/AnalysisResult';
import { useI18n } from '@/app/components/I18nProvider';
import { localeInfo } from '@/lib/i18n/config';
import { formatAnalysisPrice } from '@/lib/pricing';
import type { AnalysisResult } from '@/lib/types';

interface UnpaidDocument {
  id: string;
  fileName?: string;
}

export default function DashboardPage() {
  const { t, locale } = useI18n();
  const price = formatAnalysisPrice(localeInfo[locale].tag);
  const [unpaid, setUnpaid] = useState<UnpaidDocument[]>([]);
  const [paying, setPaying] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const handledReturn = useRef(false);

  const addUnpaid = (doc: UnpaidDocument) =>
    setUnpaid((prev) => (prev.some((d) => d.id === doc.id) ? prev : [...prev, doc]));

  const analyze = async (documentId: string, sessionId: string) => {
    setError(null);
    setAnalysis(null);
    setAnalyzing(true);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentId, sessionId }),
      });
      const data = await response.json();
      if (response.status === 402) {
        addUnpaid({ id: documentId });
        throw new Error(t.payment.notConfirmed);
      }
      if (!response.ok || !data.success) {
        throw new Error(data.error || t.dashboard.analyzeFailed);
      }
      setAnalysis(data.analysis);
      setUnpaid((prev) => prev.filter((d) => d.id !== documentId));
    } catch (e) {
      setError(e instanceof Error ? e.message : t.dashboard.analyzeFailed);
    } finally {
      setAnalyzing(false);
    }
  };

  const pay = async (documentId: string) => {
    setError(null);
    setPaying(documentId);
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentId }),
      });
      const data = await response.json();
      if (!response.ok || !data.success || !data.url) {
        throw new Error(data.error || t.payment.failed);
      }
      window.location.assign(data.url);
    } catch (e) {
      setError(e instanceof Error ? e.message : t.payment.failed);
      setPaying(null);
    }
  };

  // Back from Stripe Checkout: run the paid analysis, or offer to pay again after a cancel.
  useEffect(() => {
    if (handledReturn.current) return;
    handledReturn.current = true;

    const params = new URLSearchParams(window.location.search);
    const documentId = params.get('documentId');
    const checkout = params.get('checkout');
    const sessionId = params.get('session_id');
    if (!documentId || !checkout) return;

    window.history.replaceState(null, '', window.location.pathname);
    if (checkout === 'success' && sessionId) {
      analyze(documentId, sessionId);
    } else {
      addUnpaid({ id: documentId });
      setNotice(t.payment.cancelled);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Header />
      <main className="container py-12 space-y-8">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">{t.dashboard.title}</h1>
          <p className="text-slate-400">{t.dashboard.subtitle}</p>
        </div>

        <div className="card p-6 space-y-4">
          <p className="text-sm text-slate-300">{t.payment.notice.replace('{price}', price)}</p>
          <DocumentUpload
            onUploadSuccess={(id, fileName) => {
              setNotice(null);
              addUnpaid({ id, fileName });
            }}
            onUploadError={setError}
          />
        </div>

        {unpaid.length > 0 && (
          <div className="card p-6 space-y-3">
            {unpaid.map((doc) => (
              <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3">
                <span className="text-white">{doc.fileName ?? t.payment.yourDocument}</span>
                <button
                  onClick={() => pay(doc.id)}
                  disabled={paying !== null || analyzing}
                  className="btn btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {paying === doc.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <CreditCard className="w-4 h-4" />
                  )}
                  {paying === doc.id
                    ? t.payment.redirecting
                    : t.payment.payButton.replace('{price}', price)}
                </button>
              </div>
            ))}
          </div>
        )}

        {analyzing && (
          <div className="alert-info flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin" /> {t.dashboard.analyzing}
          </div>
        )}
        {notice && <div className="alert-warning">{notice}</div>}
        {error && <div className="alert-error">{error}</div>}
        {analysis && <AnalysisResultComponent analysis={analysis} />}
      </main>
    </>
  );
}
