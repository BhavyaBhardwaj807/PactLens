import React from 'react';
import { AlertCircle, AlertTriangle, Info, Shield } from 'lucide-react';

export default function RiskSummary({ risks, riskScore, riskLevel, riskSummary }) {
  if (!risks || risks.length === 0) {
    return null;
  }

  const highRisks = risks.filter(r => r.risk_level === 'high').length;
  const mediumRisks = risks.filter(r => r.risk_level === 'medium').length;
  const lowRisks = risks.filter(r => r.risk_level === 'low').length;

  // Determine overall risk color based on level
  const getRiskColor = () => {
    if (!riskLevel) return 'text-gray-400';
    const level = riskLevel.toLowerCase();
    if (level === 'high') return 'text-risk-high';
    if (level === 'medium') return 'text-risk-medium';
    return 'text-risk-low';
  };

  const getRiskBgColor = () => {
    if (!riskLevel) return 'bg-gray-900/20 border-gray-700/50';
    const level = riskLevel.toLowerCase();
    if (level === 'high') return 'bg-red-900/20 border-risk-high/50';
    if (level === 'medium') return 'bg-amber-900/20 border-risk-medium/50';
    return 'bg-blue-900/20 border-risk-low/50';
  };

  return (
    <div className="space-y-4">
      {/* Overall Risk Score */}
      {riskScore !== undefined && riskLevel && (
        <div className={`${getRiskBgColor()} border rounded-xl p-6`}>
          <div className="flex items-start gap-4">
            <Shield size={32} className={getRiskColor()} />
            <div className="flex-1">
              <div className="flex items-baseline gap-3 mb-2">
                <h3 className="text-xl font-semibold text-white">Overall Contract Risk</h3>
                <span className={`text-3xl font-bold ${getRiskColor()}`}>
                  {riskScore.toFixed(1)}/10
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor()}`}>
                  {riskLevel}
                </span>
              </div>
              {riskSummary && (
                <p className="text-gray-300 text-sm leading-relaxed">{riskSummary}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Risk Breakdown */}
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
    </div>
  );
}
