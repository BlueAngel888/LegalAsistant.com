import Link from "next/link";
import { redirect } from "next/navigation";
import { requireUserId } from "@/lib/auth";
import { listDocuments } from "@/lib/db";
import { StatusBadge } from "@/components/StatusBadge";
import { AutoRefresh } from "@/components/AutoRefresh";
import { countryName, documentTypeLabel } from "@/utils/constants";
import { formatBytes, formatDate } from "@/utils/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const userId = await requireUserId();
  if (!userId) redirect("/sign-in");
  const documents = await listDocuments(userId);
  const anyProcessing = documents.some((d) => d.status === "processing");

  return (
    <div className="space-y-6">
      <AutoRefresh active={anyProcessing} />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Documentele mele</h1>
        <Link href="/upload" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
          Încarcă document
        </Link>
      </div>

      {documents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
          <p className="text-slate-600">Nu ai încărcat încă niciun document.</p>
          <Link href="/upload" className="mt-3 inline-block font-medium text-indigo-600 hover:underline">
            Încarcă primul document →
          </Link>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Document</th>
                <th className="px-4 py-3">Tip</th>
                <th className="px-4 py-3">Țară</th>
                <th className="px-4 py-3">Încărcat</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((d) => (
                <tr key={d.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link href={`/documents/${d.id}`} className="font-medium text-slate-900 hover:text-indigo-600">
                      {d.file_name}
                    </Link>
                    <div className="text-xs text-slate-500">
                      {formatBytes(d.size_bytes)}
                      {d.page_count ? ` · ${d.page_count} pag.` : ""}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{documentTypeLabel(d.document_type)}</td>
                  <td className="px-4 py-3 text-slate-600">{countryName(d.country_code)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(d.created_at)}</td>
                  <td className="px-4 py-3"><StatusBadge status={d.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
