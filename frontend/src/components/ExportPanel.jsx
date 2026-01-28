import React, { useState } from 'react';
import { Download, FileText, BarChart3 } from 'lucide-react';

export default function ExportPanel({ onExport, isLoading = false }) {
  const [selectedFormat, setSelectedFormat] = useState('pdf');

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 space-y-4">
      <h3 className="font-semibold text-gray-100">Export Analysis Report</h3>

      <div className="space-y-3">
        {/* Format Selection */}
        <div>
          <label className="text-sm font-medium text-gray-300 block mb-2">
            Export Format
          </label>
          <div className="grid grid-cols-2 gap-3">
            {[
              { id: 'pdf', label: 'PDF Report', icon: FileText },
              { id: 'json', label: 'JSON Data', icon: BarChart3 },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setSelectedFormat(id)}
                className={`flex items-center gap-2 px-4 py-3 rounded-lg border transition-all ${
                  selectedFormat === id
                    ? 'bg-gradient-accent border-accent-cyan text-white'
                    : 'bg-dark-bg border-dark-border text-gray-300 hover:border-accent-cyan'
                }`}
              >
                <Icon size={18} />
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={() => onExport(selectedFormat)}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 bg-gradient-accent text-white px-4 py-3 rounded-lg font-medium hover:shadow-accent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <Download size={20} />
          {isLoading ? 'Generating...' : 'Download Report'}
        </button>
      </div>

      {/* Info */}
      <p className="text-xs text-gray-500 text-center">
        Report includes contradictions, risk assessment, and recommendations
      </p>
    </div>
  );
}
