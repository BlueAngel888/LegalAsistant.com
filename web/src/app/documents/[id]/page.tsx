import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { requireUserId } from "@/lib/auth";
import { getDocument } from "@/lib/db";
import { signedUrl } from "@/lib/storage";
import { AnalysisPanel } from "@/components/AnalysisPanel";
import { countryName, documentTypeLabel, languageName } from "@/utils/constants";
import { formatBytes, formatDate } from "@/utils/format";
import { MIN_TEXT_CHARS } from "@/lib/pdf";

export const dynamic = "force-dynamic";

export default async function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const userId = await requireUserId();
  if (!userId) redirect("/sign-in");
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();

  const doc = await getDocument(userId, id);
  if (!doc) notFound();
  const previewUrl = await signedUrl(doc.storage_path);
  const scanned = (doc.extracted_text?.length ?? 0) < MIN_TEXT_CHARS;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard" className="text-sm text-slate-500 hover:text-slate-700">← Documentele mele</Link>
        <h1 className="mt-1 break-all text-2xl font-semibold text-slate-900">{doc.file_name}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {documentTypeLabel(doc.document_type)} · {countryName(doc.country_code)} · analiză în {languageName(doc.language)} ·{" "}
          {formatBytes(doc.size_bytes)}
          {doc.page_count ? ` · ${doc.page_count} pag.` : ""} · {formatDate(doc.created_at)}
          {scanned && " · scanat (citit ca imagine)"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-4 py-2 text-sm font-medium text-slate-700">Previzualizare</div>
          <iframe src={previewUrl} title={doc.file_name} className="h-[75vh] w-full" />
        </section>
        <AnalysisPanel documentId={doc.id} initialStatus={doc.status} initialError={doc.error_message} />
      </div>
    </div>
  );
}
