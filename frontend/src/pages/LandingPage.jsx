import React from 'react';
import { ArrowRight, CheckCircle, Zap, Shield, BarChart3, Search, Upload, AlertCircle, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  const features = [
    {
      icon: <Upload size={28} className="text-accent-cyan" />,
      title: 'Multi-Document Upload',
      description: 'Upload multiple PDFs at once - contracts, offers, NDAs, policies.',
    },
    {
      icon: <Zap size={28} className="text-accent-cyan" />,
      title: 'Smart Clause Extraction',
      description: 'Intelligent parsing preserves clause context and relationships.',
    },
    {
      icon: <AlertCircle size={28} className="text-accent-cyan" />,
      title: 'Contradiction Detection',
      description: 'Find conflicts and hidden risks across all your documents.',
    },
    {
      icon: <Shield size={28} className="text-accent-cyan" />,
      title: 'Risk Categorization',
      description: 'Clear risk levels (High/Medium/Low) with plain-English explanations.',
    },
    {
      icon: <Search size={28} className="text-accent-cyan" />,
      title: 'Question-Driven Analysis',
      description: 'Ask questions about your contracts and get instant answers.',
    },
    {
      icon: <BarChart3 size={28} className="text-accent-cyan" />,
      title: 'Export & Summary',
      description: 'Generate professional PDF reports with full traceability.',
    },
  ];

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 bg-dark-bg/95 backdrop-blur-md border-b border-dark-border/50 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-gradient-accent rounded-xl flex items-center justify-center shadow-accent">
              <FileText size={24} className="text-white" />
            </div>
            <div>
              <span className="font-bold text-white text-xl tracking-tight">PactLens</span>
              <p className="text-xs text-gray-400">Legal Contract Analysis</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm">
            <a href="#features" className="text-gray-300 hover:text-accent-cyan transition-colors">Features</a>
            <a href="#how-it-works" className="text-gray-300 hover:text-accent-cyan transition-colors">How It Works</a>
          </nav>
          <Link
            to="/upload"
            className="bg-gradient-accent text-white px-6 py-2.5 rounded-lg font-semibold hover:shadow-accent transition-all duration-300 hover:scale-105"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative max-w-7xl mx-auto px-6 pt-40 pb-24">
        {/* Gradient Orbs */}
        <div className="absolute top-20 left-10 w-96 h-96 bg-accent-cyan/10 rounded-full blur-3xl"></div>
        <div className="absolute top-40 right-10 w-80 h-80 bg-accent-blue/10 rounded-full blur-3xl"></div>
        
        <div className="relative text-center space-y-8 mb-24">
          <div className="inline-block">
            <span className="px-4 py-2 bg-accent-cyan/10 border border-accent-cyan/20 rounded-full text-accent-cyan text-sm font-medium">
              ⚡ Powered by Advanced AI
            </span>
          </div>
          <h1 className="text-6xl md:text-7xl font-extrabold text-white leading-tight tracking-tight">
            Understand Your Legal{' '}
            <span className="bg-gradient-accent bg-clip-text text-transparent">Contracts</span>
          </h1>
          <p className="text-2xl text-gray-300 max-w-3xl mx-auto font-light">
            See what your contract won't tell you.
          </p>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Detect contradictions, hidden risks, and conflicts across multiple documents in seconds. Built for legal professionals and businesses.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 bg-gradient-accent text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-accent transition-all duration-300 hover:scale-105"
            >
              <Upload size={22} />
              Upload & Analyze
              <ArrowRight size={22} />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center gap-2 bg-dark-card border border-dark-border text-white px-8 py-4 rounded-xl font-semibold text-lg hover:border-accent-cyan transition-all duration-300"
            >
              <Search size={22} />
              See How It Works
            </a>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto pt-16">
            <div>
              <div className="text-4xl font-bold text-accent-cyan">100%</div>
              <div className="text-sm text-gray-400 mt-1">AI Powered</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-accent-cyan">&lt;2min</div>
              <div className="text-sm text-gray-400 mt-1">Analysis Time</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-accent-cyan">∞</div>
              <div className="text-sm text-gray-400 mt-1">Documents</div>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div id="features" className="scroll-mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 my-24">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="group bg-gradient-to-br from-dark-card to-dark-card/50 border border-dark-border rounded-2xl p-8 hover:border-accent-cyan/50 hover:shadow-accent transition-all duration-500 hover:-translate-y-2"
            >
              <div className="w-14 h-14 bg-gradient-accent rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* How It Works */}
        <section id="how-it-works" className="scroll-mt-24 my-32 relative">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold text-white mb-4">How It Works</h2>
            <p className="text-xl text-gray-400">Simple, fast, and accurate contract analysis</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { step: 1, title: 'Upload', desc: 'Drop your contract PDFs', icon: <Upload size={24} className="text-white" /> },
              { step: 2, title: 'Extract', desc: 'Smart clause parsing', icon: <FileText size={24} className="text-white" /> },
              { step: 3, title: 'Analyze', desc: 'AI contradiction detection', icon: <Zap size={24} className="text-white" /> },
              { step: 4, title: 'Report', desc: 'Get actionable insights', icon: <BarChart3 size={24} className="text-white" /> },
            ].map((item, idx) => (
              <div key={idx} className="relative">
                {idx < 3 && (
                  <div className="hidden md:block absolute top-10 left-1/2 w-full h-0.5 bg-gradient-to-r from-accent-cyan to-accent-blue"></div>
                )}
                <div className="relative bg-dark-card border border-dark-border rounded-2xl p-8 text-center hover:border-accent-cyan/50 transition-all duration-300">
                  <div className="w-20 h-20 bg-gradient-accent rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-accent">
                    {item.icon}
                  </div>
                  <div className="absolute -top-4 -right-4 w-10 h-10 bg-accent-cyan rounded-full flex items-center justify-center text-white font-bold text-lg shadow-accent">
                    {item.step}
                  </div>
                  <h3 className="font-bold text-white text-xl mb-3">{item.title}</h3>
                  <p className="text-gray-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="relative text-center space-y-8 py-20 px-8 bg-gradient-to-br from-dark-card to-dark-card/50 border border-dark-border rounded-3xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-accent opacity-5"></div>
          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Ready to analyze your contracts?</h2>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto mb-8">
              Join professionals who trust PactLens for critical contract analysis.
            </p>
            <Link
              to="/upload"
              className="inline-flex items-center gap-3 bg-gradient-accent text-white px-10 py-5 rounded-xl font-bold text-xl hover:shadow-accent transition-all duration-300 hover:scale-105"
            >
              Start Analyzing Now
              <ArrowRight size={24} />
            </Link>
            <p className="text-sm text-gray-400 mt-6">No credit card required • Free to start</p>
          </div>
        </section>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-border bg-dark-bg/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-accent rounded-lg flex items-center justify-center">
                <FileText size={20} className="text-white" />
              </div>
              <div>
                <span className="font-bold text-white text-lg">PactLens</span>
                <p className="text-xs text-gray-400">Legal Contract Analysis</p>
              </div>
            </div>
            <p className="text-gray-400 text-sm max-w-md text-center">
              <strong className="text-white">Disclaimer:</strong> PactLens is for informational purposes only and is NOT legal advice.
            </p>
            <p className="text-gray-500 text-sm">© 2026 PactLens. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
