import { SignUpButton, SignInButton } from '@clerk/nextjs';
import Link from 'next/link';
import { ArrowRight, Shield, Zap, FileText, BarChart3 } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow">
        <nav className="container py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-blue-600" />
            <span className="text-2xl font-bold text-gray-900">Legal Assistant</span>
          </div>
          <div className="flex gap-4">
            <SignInButton mode="modal">
              <button className="btn btn-secondary">Sign In</button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="btn btn-primary">Get Started</button>
            </SignUpButton>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              AI-Powered Legal Document Analysis
            </h1>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Upload your contracts, NDAs, and legal documents to get instant AI-powered analysis.
              Identify strengths, weaknesses, risks, and defense strategies with Claude AI.
            </p>
            <div className="flex gap-4">
              <SignUpButton mode="modal">
                <button className="btn btn-primary btn-large">
                  Start Analyzing <ArrowRight className="ml-2 w-5 h-5" />
                </button>
              </SignUpButton>
              <Link href="#features">
                <button className="btn btn-secondary btn-large">Learn More</button>
              </Link>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-xl p-8 border-2 border-blue-200">
            <div className="space-y-4">
              <div className="h-64 bg-gradient-to-br from-blue-100 to-indigo-200 rounded-lg flex items-center justify-center">
                <FileText className="w-24 h-24 text-blue-400" />
              </div>
              <p className="text-sm text-gray-600 text-center">
                Drag and drop your documents here or upload from your computer
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white py-20">
        <div className="container">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-900">
            Powerful Features
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: <Zap className="w-8 h-8 text-yellow-500" />,
                title: 'Instant Analysis',
                desc: 'Get comprehensive analysis in seconds using advanced AI',
              },
              {
                icon: <Shield className="w-8 h-8 text-blue-600" />,
                title: 'Secure',
                desc: 'Your documents are encrypted and stored securely',
              },
              {
                icon: <BarChart3 className="w-8 h-8 text-green-500" />,
                title: 'Multi-Jurisdictional',
                desc: 'Support for EU and US jurisdictions',
              },
              {
                icon: <FileText className="w-8 h-8 text-purple-500" />,
                title: 'Multiple Formats',
                desc: 'Supports PDF, Word, and text documents',
              },
            ].map((feature, idx) => (
              <div key={idx} className="card p-6 hover:shadow-lg transition">
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="container py-20">
        <h2 className="text-4xl font-bold text-center mb-12 text-gray-900">
          What You Get
        </h2>
        <div className="grid md:grid-cols-2 gap-8">
          {[
            { title: 'Jurisdiction Detection', desc: 'Automatically identifies applicable jurisdictions' },
            { title: 'Strengths & Weaknesses', desc: 'Detailed analysis of document strengths and weaknesses' },
            { title: 'Legal Errors', desc: 'Identifies potential legal issues and errors' },
            { title: 'Defense Strategy', desc: 'Provides recommended defense strategies' },
            { title: 'Risk Assessment', desc: 'Evaluates risk levels from low to critical' },
            { title: 'Multi-Language', desc: 'Supports Romanian, English, and other languages' },
          ].map((item, idx) => (
            <div key={idx} className="card p-6 border-l-4 border-blue-600">
              <h3 className="text-xl font-semibold mb-2 text-gray-900">{item.title}</h3>
              <p className="text-gray-600">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-16">
        <div className="container text-center text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to Analyze Your Documents?</h2>
          <p className="text-xl mb-8 opacity-90">
            Get started for free. No credit card required.
          </p>
          <SignUpButton mode="modal">
            <button className="btn bg-white text-blue-600 hover:bg-gray-100 font-semibold px-8 py-3 rounded-md">
              Create Free Account
            </button>
          </SignUpButton>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-8">
        <div className="container">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-white font-bold mb-4">Legal Assistant</h4>
              <p className="text-sm">AI-powered legal document analysis platform</p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Product</h4>
              <ul className="text-sm space-y-2">
                <li><a href="#" className="hover:text-white">Features</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
                <li><a href="#" className="hover:text-white">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Company</h4>
              <ul className="text-sm space-y-2">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="text-sm space-y-2">
                <li><a href="#" className="hover:text-white">Privacy</a></li>
                <li><a href="#" className="hover:text-white">Terms</a></li>
                <li><a href="#" className="hover:text-white">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-8 text-center text-sm">
            <p>&copy; 2024 Legal Assistant. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
