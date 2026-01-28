import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText } from 'lucide-react';

export default function Header() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <header className="fixed top-16 left-0 right-0 bg-dark-bg/80 backdrop-blur-md border-b border-dark-border z-40">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-10 h-10 bg-gradient-accent rounded-lg flex items-center justify-center group-hover:shadow-accent transition-all">
            <FileText size={24} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg">PactLens</h1>
            <p className="text-xs text-gray-400">Legal Contract Analysis</p>
          </div>
        </Link>

        <nav className="flex items-center gap-6">
          <Link
            to="/"
            className={`text-sm font-medium transition-colors ${
              isActive('/') ? 'text-accent-cyan' : 'text-gray-400 hover:text-gray-100'
            }`}
          >
            Home
          </Link>
          <Link
            to="/upload"
            className={`text-sm font-medium transition-colors ${
              isActive('/upload') ? 'text-accent-cyan' : 'text-gray-400 hover:text-gray-100'
            }`}
          >
            Upload
          </Link>
        </nav>
      </div>
    </header>
  );
}
