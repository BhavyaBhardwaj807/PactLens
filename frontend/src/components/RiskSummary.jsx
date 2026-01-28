import React from 'react';
import { AlertCircle, AlertTriangle, Info } from 'lucide-react';

export default function RiskSummary({ risks }) {
  if (!risks || risks.length === 0) {
    return null;
  }

  const highRisks = risks.filter(r => r.risk_level === 'high').length;
  const mediumRisks = risks.filter(r => r.risk_level === 'medium').length;
  const lowRisks = risks.filter(r => r.risk_level === 'low').length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* High Risk */}
      <div className="bg-red-900/20 border border-risk-high/50 rounded-xl p-4">
        <div className="flex items-center gap-3 mb-2">
          <AlertCircle size={24} className="text-risk-high" />
          <div>
            <p className="text-sm font-medium text-gray-400">High Risk</p>
            <p className="text-2xl font-bold text-risk-high">{highRisks}</p>
          </div>
        </div>
        <p className="text-xs text-gray-400">Legal traps & penalties</p>
      </div>

      {/* Medium Risk */}
      <div className="bg-amber-900/20 border border-risk-medium/50 rounded-xl p-4">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle size={24} className="text-risk-medium" />
          <div>
            <p className="text-sm font-medium text-gray-400">Medium Risk</p>
            <p className="text-2xl font-bold text-risk-medium">{mediumRisks}</p>
          </div>
        </div>
        <p className="text-xs text-gray-400">Ambiguous language</p>
      </div>

      {/* Low Risk */}
      <div className="bg-blue-900/20 border border-risk-low/50 rounded-xl p-4">
        <div className="flex items-center gap-3 mb-2">
          <Info size={24} className="text-risk-low" />
          <div>
            <p className="text-sm font-medium text-gray-400">Low Risk</p>
            <p className="text-2xl font-bold text-risk-low">{lowRisks}</p>
          </div>
        </div>
        <p className="text-xs text-gray-400">Informational mismatches</p>
      </div>
    </div>
  );
}
