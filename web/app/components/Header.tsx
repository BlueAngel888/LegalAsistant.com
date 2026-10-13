'use client';

import Link from 'next/link';
import { UserButton } from '@clerk/nextjs';
import { Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow sticky top-0 z-50">
      <nav className="container py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition">
          <Shield className="w-8 h-8 text-blue-600" />
          <span className="text-2xl font-bold text-gray-900">Legal Assistant</span>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-8">
          <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
            Dashboard
          </Link>
          <Link href="/documents" className="text-gray-600 hover:text-gray-900">
            Documents
          </Link>
          <Link href="/pricing" className="text-gray-600 hover:text-gray-900">
            Pricing
          </Link>
          <div className="pl-8 border-l border-gray-200">
            <UserButton />
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2"
        >
          {mobileMenuOpen ? (
            <X className="w-6 h-6 text-gray-600" />
          ) : (
            <Menu className="w-6 h-6 text-gray-600" />
          )}
        </button>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="absolute top-full left-0 right-0 bg-white border-b border-gray-200 md:hidden">
            <div className="container py-4 space-y-4">
              <Link href="/dashboard" className="block text-gray-600 hover:text-gray-900">
                Dashboard
              </Link>
              <Link href="/documents" className="block text-gray-600 hover:text-gray-900">
                Documents
              </Link>
              <Link href="/pricing" className="block text-gray-600 hover:text-gray-900">
                Pricing
              </Link>
              <div className="pt-4 border-t border-gray-200">
                <UserButton />
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
