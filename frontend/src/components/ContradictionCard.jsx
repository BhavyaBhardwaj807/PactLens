import React from 'react';
import { AlertCircle, AlertTriangle, Info, ChevronDown } from 'lucide-react';
import { useState } from 'react';

export default function ContradictionCard({ contradiction }) {
  const [expanded, setExpanded] = useState(false);

  const getRiskColor = (level) => {
    switch (level) {
      case 'high':
        return 'bg-red-900/20 border-risk-high text-risk-high';
      case 'medium':
        return 'bg-amber-900/20 border-risk-medium text-risk-medium';
      case 'low':
        return 'bg-blue-900/20 border-risk-low text-risk-low';
      default:
        return 'bg-gray-900/20 border-gray-600 text-gray-300';
    }
  };

  const getRiskIcon = (level) => {
    switch (level) {
      case 'high':
        return <AlertCircle size={18} />;
      case 'medium':
        return <AlertTriangle size={18} />;
      case 'low':
        return <Info size={18} />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl overflow-hidden hover:shadow-card transition-all">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-5 text-left hover:bg-dark-bg/50 transition-colors flex justify-between items-start gap-4"
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span
              className={`badge-high badge-medium badge-low flex items-center gap-2 px-3 py-1 rounded-lg border ${getRiskColor(
                contradiction.risk_level
              )}`}
            >
              {getRiskIcon(contradiction.risk_level)}
              {contradiction.risk_level.charAt(0).toUpperCase() + contradiction.risk_level.slice(1)} Risk
            </span>
          </div>
          <h3 className="text-base font-semibold text-gray-100 mb-1">
            {contradiction.title}
          </h3>
          <p className="text-sm text-gray-400">{contradiction.summary}</p>
        </div>
        <ChevronDown
          size={20}
          className={`text-gray-400 transition-transform flex-shrink-0 ${
            expanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {expanded && (
        <div className="border-t border-dark-border px-5 py-4 space-y-4 bg-dark-bg/30">
          {/* Clause Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {contradiction.clauses?.map((clause, idx) => (
              <div key={idx} className="bg-dark-bg rounded-lg p-4 border border-dark-border">
                <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-2">
                  {clause.document} - {clause.clause_type}
                </p>
                <p className="text-sm text-gray-200 leading-relaxed">{clause.text}</p>
                <p className="text-xs text-gray-500 mt-2">Section {clause.section}</p>
              </div>
            ))}
          </div>

          {/* Risk Explanation */}
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <h4 className="font-semibold text-gray-100 mb-2">Why This Matters</h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              {contradiction.risk_explanation}
            </p>
          </div>

          {/* Indian Law Context */}
          {contradiction.indian_law_note && (
            <div className="bg-accent-cyan/5 rounded-lg p-4 border border-accent-cyan/30">
              <h4 className="font-semibold text-accent-cyan mb-2 flex items-center gap-2">
                <Info size={16} />
                Indian Law Context
              </h4>
              <p className="text-sm text-gray-300">
                {contradiction.indian_law_note}
              </p>
            </div>
          )}

          {/* Action Items */}
          {contradiction.recommendations && (
            <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
              <h4 className="font-semibold text-gray-100 mb-3">Recommendations</h4>
              <ul className="space-y-2">
                {contradiction.recommendations.map((rec, idx) => (
                  <li key={idx} className="text-sm text-gray-300 flex gap-2">
                    <span className="text-accent-cyan mt-1">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
