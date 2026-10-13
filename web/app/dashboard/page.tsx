'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Header } from '@/app/components/Header';
import { DocumentUpload } from '@/app/components/DocumentUpload';
import { AnalysisResultComponent } from '@/app/components/AnalysisResult';
import { useI18n } from '@/app/components/I18nProvider';
import type { AnalysisResult } from '@/lib/types';

export default function DashboardPage() {
  const { t } = useI18n();
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);

  const analyze = async (documentId: string) => {
    setError(null);
    setAnalysis(null);
    setAnalyzing(true);
    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentId }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error || t.dashboard.analyzeFailed);
      }
      setAnalysis(data.analysis);
    } catch (e) {
      setError(e instanceof Error ? e.message : t.dashboard.analyzeFailed);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <>
      <Header />
      <main className="container py-12 space-y-8">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-2">{t.dashboard.title}</h1>
          <p className="text-slate-400">{t.dashboard.subtitle}</p>
        </div>

        <div className="card p-6">
          <DocumentUpload onUploadSuccess={analyze} onUploadError={setError} />
        </div>

        {analyzing && (
          <div className="alert-info flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin" /> {t.dashboard.analyzing}
          </div>
        )}
        {error && <div className="alert-error">{error}</div>}
        {analysis && <AnalysisResultComponent analysis={analysis} />}
      </main>
    </>
  );
}
