import { UploadForm } from "@/components/UploadForm";

export default function UploadPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Încarcă un document</h1>
        <p className="mt-1 text-sm text-slate-600">
          PDF, maxim {process.env.MAX_UPLOAD_MB || 4} MB. Alege țara a cărei legislație se aplică și limba în care vrei analiza.
        </p>
      </div>
      <UploadForm maxMb={Number(process.env.MAX_UPLOAD_MB || 4)} />
    </div>
  );
}
