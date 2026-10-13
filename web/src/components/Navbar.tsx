import Link from "next/link";
import { Show, SignInButton, SignUpButton, UserButton } from "@clerk/nextjs";

export function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-indigo-600 text-sm text-white">LA</span>
          LegalAssistant
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Show when="signed-in">
            <Link href="/dashboard" className="text-slate-600 hover:text-slate-900">Documentele mele</Link>
            <Link href="/upload" className="rounded-md bg-indigo-600 px-3 py-1.5 font-medium text-white hover:bg-indigo-700">
              Încarcă document
            </Link>
            <UserButton>
              <UserButton.MenuItems>
                <UserButton.Link label="Profil" labelIcon={<span>👤</span>} href="/profile" />
              </UserButton.MenuItems>
            </UserButton>
          </Show>
          <Show when="signed-out">
            <SignInButton mode="redirect">
              <button className="text-slate-600 hover:text-slate-900">Autentificare</button>
            </SignInButton>
            <SignUpButton mode="redirect">
              <button className="rounded-md bg-indigo-600 px-3 py-1.5 font-medium text-white hover:bg-indigo-700">
                Creează cont
              </button>
            </SignUpButton>
          </Show>
        </div>
      </nav>
    </header>
  );
}
