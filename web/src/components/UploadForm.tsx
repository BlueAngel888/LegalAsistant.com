"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { COUNTRIES, DOCUMENT_TYPES, LANGUAGES } from "@/utils/constants";
import { formatBytes } from "@/utils/format";
import { Spinner } from "./Spinner";

export function UploadForm({ maxMb }: { maxMb: number }) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [country, setCountry] = useState("RO");
  const [documentType, setDocumentType] = useState("contract");
  const [language, setLanguage] = useState("ro");
  const [analyzeNow, setAnalyzeNow] = useState(true);
  const [busy, setBusy] = useState<null | "upload" | "analyze">(null);
  const [error, setError] = useState<string | null>(null);

  function pick(f: File | undefined | null) {
    setError(null);
    if (!f) return;
    if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
      setError("Momentan acceptăm doar fișiere PDF.");
      return;
    }
    if (f.size > maxMb * 1024 * 1024) {
      setError(`Fișierul depășește ${maxMb} MB.`);
      return;
    }
    setFile(f);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setBusy("upload");
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("country", country);
      fd.append("documentType", documentType);
      fd.append("language", language);
      const res = await fetch("/api/documents/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Încărcarea a eșuat.");
      const id: string = data.document.id;

      if (analyzeNow) {
        setBusy("analyze");
        const a = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ documentId: id }),
        });
        if (!a.ok) {
          const ad = await a.json().catch(() => ({}));
          throw new Error(ad.error || "Pornirea analizei a eșuat.");
        }
      }
      router.push(`/documents/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "A apărut o eroare.");
      setBusy(null);
    }
  }

  const selectClass =
    "mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

  return (
    <form onSubmit={submit} className="space-y-5 rounded-xl border border-slate-200 bg-white p-6">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0]);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 text-center transition ${
          dragging ? "border-indigo-500 bg-indigo-50" : "border-slate-300 hover:border-indigo-400"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => pick(e.target.files?.[0])}
        />
        {file ? (
          <>
            <p className="font-medium text-slate-900">{file.name}</p>
            <p className="text-sm text-slate-500">{formatBytes(file.size)} · click pentru a schimba</p>
          </>
        ) : (
          <>
            <p className="font-medium text-slate-900">Trage PDF-ul aici</p>
            <p className="text-sm text-slate-500">sau click pentru a alege un fișier</p>
          </>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <label className="text-sm font-medium text-slate-700">
          Țara (legislația)
          <select className={selectClass} value={country} onChange={(e) => setCountry(e.target.value)}>
            {COUNTRIES.map((c) => (
              <option key={c.code} value={c.code}>{c.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Tipul documentului
          <select className={selectClass} value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
            {DOCUMENT_TYPES.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Limba analizei
          <select className={selectClass} value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-700">
        <input type="checkbox" checked={analyzeNow} onChange={(e) => setAnalyzeNow(e.target.checked)} />
        Pornește analiza imediat după încărcare
      </label>

      {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <button
        type="submit"
        disabled={!file || busy !== null}
        className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-indigo-600 px-4 py-2.5 font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy && <Spinner />}
        {busy === "upload" ? "Se încarcă…" : busy === "analyze" ? "Se pornește analiza…" : "Încarcă"}
      </button>
    </form>
  );
}
