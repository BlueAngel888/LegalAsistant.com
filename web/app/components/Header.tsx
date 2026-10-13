'use client';

import Link from 'next/link';
import { UserButton } from '@clerk/nextjs';
import { Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="bg-slate-950/70 backdrop-blur-xl border-b border-white/10 sticky top-0 z-50">
      <nav className="container py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition">
          <Shield className="w-8 h-8 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.7)]" />
          <span className="text-2xl font-bold text-white">Legal Assistant</span>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-8">
          <Link href="/dashboard" className="text-slate-300 hover:text-white">
            Dashboard
          </Link>
          <Link href="/documents" className="text-slate-300 hover:text-white">
            Documents
          </Link>
          <Link href="/pricing" className="text-slate-300 hover:text-white">
            Pricing
          </Link>
          <div className="pl-8 border-l border-white/10">
            <UserButton />
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2"
        >
          {mobileMenuOpen ? (
            <X className="w-6 h-6 text-slate-300" />
          ) : (
            <Menu className="w-6 h-6 text-slate-300" />
          )}
        </button>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="absolute top-full left-0 right-0 bg-white/5 border-b border-white/10 md:hidden">
            <div className="container py-4 space-y-4">
              <Link href="/dashboard" className="block text-slate-300 hover:text-white">
                Dashboard
              </Link>
              <Link href="/documents" className="block text-slate-300 hover:text-white">
                Documents
              </Link>
              <Link href="/pricing" className="block text-slate-300 hover:text-white">
                Pricing
              </Link>
              <div className="pt-4 border-t border-white/10">
                <UserButton />
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
