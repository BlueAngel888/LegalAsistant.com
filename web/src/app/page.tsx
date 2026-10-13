import Link from "next/link";
import { Show } from "@clerk/nextjs";

const FEATURES = [
  { title: "Puncte forte și slabe", text: "Ce joacă în favoarea ta și ce te poate dezavantaja, explicat pe înțeles." },
  { title: "Erori și vicii de formă", text: "Elemente obligatorii lipsă, termene greșite, posibile motive de nulitate." },
  { title: "Strategii de apărare", text: "Pași concreți, cu temeiul legal și termenele până la care trebuie făcuți." },
];

export default function Home() {
  return (
    <div className="space-y-14 py-6">
      <section className="space-y-5 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Analiza documentelor juridice, <span className="text-indigo-600">în câteva minute</span>
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-slate-600">
          Încarcă un contract, o amendă sau o hotărâre judecătorească. Primești o analiză bazată pe
          legislația țării tale: puncte forte, puncte slabe, erori și strategii de apărare.
        </p>
        <div className="flex justify-center gap-3">
          <Show when="signed-in">
            <Link href="/upload" className="rounded-md bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700">
              Încarcă un document
            </Link>
          </Show>
          <Show when="signed-out">
            <Link href="/sign-up" className="rounded-md bg-indigo-600 px-5 py-2.5 font-medium text-white hover:bg-indigo-700">
              Începe gratuit
            </Link>
            <Link href="/sign-in" className="rounded-md border border-slate-300 bg-white px-5 py-2.5 font-medium text-slate-700 hover:bg-slate-50">
              Am deja cont
            </Link>
          </Show>
        </div>
      </section>
      <section className="grid gap-4 sm:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold text-slate-900">{f.title}</h3>
            <p className="mt-1.5 text-sm text-slate-600">{f.text}</p>
          </div>
        ))}
      </section>
      <p className="text-center text-xs text-slate-500">
        Analiza este automată și preliminară, nu constituie consultanță juridică. Verifică-o cu un avocat înainte de a acționa.
      </p>
    </div>
  );
}
