import type { LegalAnalysis } from "@/lib/analysis-schema";

type Level = "low" | "medium" | "high";
const LEVEL_LABEL: Record<Level, string> = { low: "scăzut", medium: "mediu", high: "ridicat" };
const LEVEL_CLASS: Record<Level, string> = {
  low: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  high: "bg-rose-100 text-rose-800",
};

function Pill({ level, prefix }: { level: Level; prefix?: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${LEVEL_CLASS[level]}`}>
      {prefix ? `${prefix}: ` : ""}
      {LEVEL_LABEL[level]}
    </span>
  );
}

function Section({ title, children, empty }: { title: string; children: React.ReactNode; empty: boolean }) {
  if (empty) return null;
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      {children}
    </div>
  );
}

function Points({
  items,
  tone,
}: {
  items: { title: string; explanation: string; legal_basis: string; severity?: Level }[];
  tone: string;
}) {
  return (
    <ul className="space-y-2">
      {items.map((p, i) => (
        <li key={i} className={`rounded-lg border-l-4 bg-slate-50 p-3 ${tone}`}>
          <div className="flex items-start justify-between gap-2">
            <p className="font-medium text-slate-900">{p.title}</p>
            {p.severity && <Pill level={p.severity} prefix="gravitate" />}
          </div>
          <p className="mt-1 text-sm text-slate-700">{p.explanation}</p>
          <p className="mt-1 text-xs text-slate-500">Temei: {p.legal_basis}</p>
        </li>
      ))}
    </ul>
  );
}

export function AnalysisReport({
  analysis: a,
  meta,
}: {
  analysis: LegalAnalysis;
  meta: { model: string; from_cache: boolean; review_status: string; created_at: string };
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          <Pill level={a.risk_level} prefix="Risc" />
          <Pill level={a.confidence} prefix="Încredere" />
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">{a.document_type_detected}</span>
          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">{a.jurisdiction}</span>
        </div>
        <p className="text-slate-800">{a.summary}</p>
      </div>

      <Section title="Termene și acțiuni" empty={!a.deadlines_and_actions.length}>
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
          {a.deadlines_and_actions.map((d, i) => (
            <li key={i} className="flex items-start justify-between gap-3 p-3 text-sm">
              <div>
                <p className="font-medium text-slate-900">{d.action}</p>
                <p className="text-slate-600">{d.deadline}</p>
              </div>
              <Pill level={d.urgency} prefix="urgență" />
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Puncte forte" empty={!a.strengths.length}>
        <Points items={a.strengths} tone="border-emerald-400" />
      </Section>
      <Section title="Puncte slabe" empty={!a.weaknesses.length}>
        <Points items={a.weaknesses} tone="border-amber-400" />
      </Section>
      <Section title="Posibile erori" empty={!a.potential_errors.length}>
        <Points items={a.potential_errors} tone="border-rose-400" />
      </Section>

      <Section title="Strategii de apărare" empty={!a.defense_strategies.length}>
        <div className="space-y-3">
          {a.defense_strategies.map((s, i) => (
            <div key={i} className="rounded-lg border border-slate-200 p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-slate-900">{s.title}</p>
                <Pill level={s.likelihood_of_success} prefix="șanse" />
              </div>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700">
                {s.steps.map((step, j) => <li key={j}>{step}</li>)}
              </ol>
              <p className="mt-2 text-xs text-slate-500">Temei: {s.legal_basis}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Părți" empty={!a.parties.length}>
        <ul className="text-sm text-slate-700">
          {a.parties.map((p, i) => <li key={i}><span className="font-medium">{p.name}</span> — {p.role}</li>)}
        </ul>
      </Section>
      <Section title="Date importante" empty={!a.key_dates.length}>
        <ul className="text-sm text-slate-700">
          {a.key_dates.map((d, i) => <li key={i}><span className="font-medium">{d.date}</span> — {d.description}</li>)}
        </ul>
      </Section>
      <Section title="Legislație citată" empty={!a.legal_references.length}>
        <ul className="space-y-1 text-sm text-slate-700">
          {a.legal_references.map((r, i) => <li key={i}><span className="font-medium">{r.reference}</span> — {r.relevance}</li>)}
        </ul>
      </Section>
      <Section title="Informații lipsă" empty={!a.missing_information.length}>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
          {a.missing_information.map((m, i) => <li key={i}>{m}</li>)}
        </ul>
      </Section>

      <p className="rounded-md bg-slate-100 p-3 text-xs text-slate-600">{a.disclaimer}</p>
      <p className="text-xs text-slate-400">
        {meta.model}
        {meta.from_cache ? " · din cache" : ""} · verificare avocat: {meta.review_status === "pending" ? "în așteptare" : meta.review_status}
      </p>
    </div>
  );
}
