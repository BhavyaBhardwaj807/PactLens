import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function Disclaimer() {
  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-900/30 border-b border-yellow-600/50 backdrop-blur-sm z-50">
      <div className="max-w-7xl mx-auto px-4 py-2 flex items-center gap-3">
        <AlertCircle size={18} className="text-yellow-500 flex-shrink-0" />
        <p className="text-sm text-yellow-100">
          <strong>Disclaimer:</strong> PactLens provides informational analysis only and is NOT a substitute for legal advice. 
          Always consult a qualified legal professional before making decisions based on contract analysis.
        </p>
      </div>
    </div>
  );
}
