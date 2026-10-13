"use client";

import { useCallback, useEffect, useState } from "react";
import type { DocumentStatus } from "@/lib/types";
import type { LegalAnalysis } from "@/lib/analysis-schema";
import { AnalysisReport } from "./AnalysisReport";
import { StatusBadge } from "./StatusBadge";
import { Spinner } from "./Spinner";

interface AnalysisPayload {
  id: string;
  result: LegalAnalysis;
  model: string;
  prompt_version: string;
  from_cache: boolean;
  review_status: string;
  created_at: string;
}

export function AnalysisPanel({
  documentId,
  initialStatus,
  initialError,
}: {
  documentId: string;
  initialStatus: DocumentStatus;
  initialError: string | null;
}) {
  const [status, setStatus] = useState<DocumentStatus>(initialStatus);
  const [error, setError] = useState<string | null>(initialError);
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    const res = await fetch(`/api/analyze/${documentId}`, { cache: "no-store" });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "Nu am putut încărca analiza.");
      return;
    }
    setStatus(data.status);
    setError(data.error);
    setAnalysis(data.analysis);
  }, [documentId]);

  useEffect(() => {
    if (initialStatus === "analyzed") load();
  }, [initialStatus, load]);

  // Poll while the analysis is running.
  useEffect(() => {
    if (status !== "processing") return;
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [status, load]);

  async function start(force = false) {
    setStarting(true);
    setError(null);
    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ documentId, force }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Pornirea analizei a eșuat.");
      setStatus(data.status);
      if (data.status === "analyzed") await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "A apărut o eroare.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
        <span className="text-sm font-medium text-slate-700">Analiză</span>
        <StatusBadge status={status} />
      </div>
      <div className="p-4">
        {status === "uploaded" && (
          <div className="space-y-3 py-6 text-center">
            <p className="text-slate-600">Documentul nu a fost încă analizat.</p>
            <button
              onClick={() => start()}
              disabled={starting}
              className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {starting && <Spinner />} Analizează documentul
            </button>
          </div>
        )}

        {status === "processing" && (
          <div className="flex flex-col items-center gap-3 py-10 text-slate-600">
            <Spinner className="h-8 w-8 text-indigo-600" />
            <p>Analizăm documentul pe baza legislației selectate.</p>
            <p className="text-xs text-slate-500">Durează de obicei 1–3 minute. Poți închide pagina, rezultatul se salvează.</p>
          </div>
        )}

        {status === "failed" && (
          <div className="space-y-3 py-6 text-center">
            <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error || "Analiza a eșuat."}</p>
            <button
              onClick={() => start(true)}
              disabled={starting}
              className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {starting && <Spinner />} Încearcă din nou
            </button>
          </div>
        )}

        {status === "analyzed" && !analysis && (
          <div className="flex justify-center py-10"><Spinner className="h-6 w-6 text-indigo-600" /></div>
        )}

        {status === "analyzed" && analysis && <AnalysisReport analysis={analysis.result} meta={analysis} />}

        {error && status !== "failed" && <p className="mt-3 text-sm text-rose-700">{error}</p>}
      </div>
    </section>
  );
}
