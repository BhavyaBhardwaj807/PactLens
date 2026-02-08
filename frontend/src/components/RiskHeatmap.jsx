import React from 'react';

const RiskHeatmap = ({ heatmap, topRiskyCategory }) => {
  if (!heatmap || heatmap.length === 0) {
    return null;
  }

  // Calculate overall risk from heatmap
  const totalScore = heatmap.reduce((sum, item) => sum + item.risk_score, 0);
  const overallScore = Math.min(10, (totalScore / (heatmap.length * 3)) * 10);
  
  const getGaugeRotation = (score) => {
    return (score / 10) * 180 - 90;
  };

  const getScoreLabel = (score) => {
    if (score < 3.3) return 'LOW';
    if (score < 6.7) return 'MEDIUM';
    return 'HIGH';
  };

  const getBadgeColor = (level) => {
    switch (level) {
      case 'high':
        return 'bg-red-900/60 text-red-200';
      case 'medium':
        return 'bg-amber-900/60 text-amber-200';
      default:
        return 'bg-slate-800/60 text-slate-200';
    }
  };

  return (
    <div className="space-y-8">
      {/* Risk Gauge - Larger and Cleaner */}
      <div className="flex flex-col items-center py-6">
        <svg viewBox="0 0 200 140" width="280" height="196" className="drop-shadow-lg">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#1e40af" />
              <stop offset="33%" stopColor="#ea580c" />
              <stop offset="100%" stopColor="#dc2626" />
            </linearGradient>
          </defs>

          {/* Main gauge arc */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="20"
            strokeLinecap="round"
          />

          {/* Background arc */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke="#374151"
            strokeWidth="20"
            strokeLinecap="round"
            opacity="0.15"
          />

          {/* Needle */}
          <g transform={`rotate(${getGaugeRotation(overallScore)} 100 100)`}>
            <line x1="100" y1="100" x2="100" y2="20" stroke="#06b6d4" strokeWidth="5" strokeLinecap="round" />
            <circle cx="100" cy="100" r="7" fill="#06b6d4" />
          </g>

          {/* Labels - Better positioned */}
          <text x="25" y="125" fontSize="13" fill="#9ca3af" fontWeight="600" textAnchor="middle">LOW</text>
          <text x="100" y="125" fontSize="13" fill="#9ca3af" fontWeight="600" textAnchor="middle">MED</text>
          <text x="175" y="125" fontSize="13" fill="#9ca3af" fontWeight="600" textAnchor="middle">HIGH</text>
        </svg>

        {/* Score Display - Below gauge */}
        <div className="text-center mt-6 space-y-2">
          <div className="text-5xl font-bold text-cyan-400">{overallScore.toFixed(1)}</div>
          <div className="text-xs text-gray-500 tracking-wide">OVERALL RISK SCORE</div>
          <div className="text-sm font-semibold text-gray-300">{getScoreLabel(overallScore)} RISK</div>
        </div>
      </div>

      {/* Divider */}
      <div className="h-px bg-dark-border"></div>

      {/* Clause Breakdown */}
      <div className="space-y-4">
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Breakdown by Clause</h4>
          {topRiskyCategory && (
            <p className="text-xs text-gray-500">
              Highest risk: <span className="text-cyan-400 font-medium">{topRiskyCategory}</span>
            </p>
          )}
        </div>

        <div className="space-y-3">
          {heatmap.map((item, idx) => (
            <div key={idx} className="bg-dark-border/20 border border-dark-border/40 rounded-lg p-3">
              <div className="flex items-center justify-between mb-3">
                <h5 className="text-sm font-medium text-gray-200">{item.clause_type}</h5>
                <span className="text-sm text-gray-400 font-semibold">{item.risk_score}</span>
              </div>
              <div className="flex gap-2 flex-wrap">
                {item.high > 0 && (
                  <span className={`${getBadgeColor('high')} px-2.5 py-1 rounded text-xs font-medium`}>
                    {item.high} high
                  </span>
                )}
                {item.medium > 0 && (
                  <span className={`${getBadgeColor('medium')} px-2.5 py-1 rounded text-xs font-medium`}>
                    {item.medium} med
                  </span>
                )}
                {item.low > 0 && (
                  <span className={`${getBadgeColor('low')} px-2.5 py-1 rounded text-xs font-medium`}>
                    {item.low} low
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskHeatmap;
