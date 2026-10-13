import type { DocumentStatus } from "@/lib/types";

const STYLES: Record<DocumentStatus, { label: string; className: string }> = {
  uploaded: { label: "Încărcat", className: "bg-slate-100 text-slate-700" },
  processing: { label: "Se analizează…", className: "bg-amber-100 text-amber-800" },
  analyzed: { label: "Analizat", className: "bg-emerald-100 text-emerald-800" },
  failed: { label: "Eșuat", className: "bg-rose-100 text-rose-800" },
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const s = STYLES[status];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${s.className}`}>
      {s.label}
    </span>
  );
}
