import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import ContradictionCard from '../components/ContradictionCard';
import QuestionBox from '../components/QuestionBox';
import ExportPanel from '../components/ExportPanel';
import RiskSummary from '../components/RiskSummary';
import RiskHeatmap from '../components/RiskHeatmap';
import { analysisAPI } from '../utils/api';
import { Loader } from 'lucide-react';

export default function ResultsPage() {
  const location = useLocation();
  const { analysis, docIds } = location.state || {};

  const [contradictions, setContradictions] = useState(analysis?.contradictions || []);
  const [answers, setAnswers] = useState([]);
  const [isAsking, setIsAsking] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState('');
  const [showHeatmap, setShowHeatmap] = useState(false);

  useEffect(() => {
    if (!analysis) {
      setError('No analysis data available. Please upload documents first.');
    }
  }, [analysis]);

  const handleAskQuestion = async (question) => {
    setIsAsking(true);
    setError('');

    try {
      const response = await analysisAPI.askQuestion(question);
      setAnswers([
        {
          question,
          answer: response.data.answer,
          evidence: response.data.evidence,
        },
        ...answers,
      ]);
    } catch (err) {
      setError('Failed to answer question. Please try again.');
      console.error(err);
    } finally {
      setIsAsking(false);
    }
  };

  const handleExport = async (format) => {
    setIsExporting(true);
    try {
      const response = await analysisAPI.exportReport(format);
      // Handle file download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `pactlens-report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentElement.removeChild(link);
    } catch (err) {
      setError('Failed to export report. Please try again.');
      console.error(err);
    } finally {
      setIsExporting(false);
    }
  };

  if (error && !analysis) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-32 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-risk-high text-lg">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-dark pt-20">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-2">Analysis Results</h1>
          <p className="text-gray-400">
            {contradictions.length} contradiction{contradictions.length !== 1 ? 's' : ''} detected
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-risk-high/10 border border-risk-high/50 rounded-lg p-4 text-risk-high">
            {error}
          </div>
        )}

        {/* Risk Summary */}
        <div className="mb-8">
          <RiskSummary 
            risks={contradictions}
            riskScore={analysis?.risk_score}
            riskLevel={analysis?.risk_level}
            riskSummary={analysis?.risk_summary}
          />
        </div>

        {/* Heatmap Toggle Button */}
        {analysis?.heatmap && !showHeatmap && (
          <div className="mb-8 flex justify-center">
            <button
              onClick={() => setShowHeatmap(true)}
              className="px-6 py-3 bg-gradient-to-r from-accent-cyan to-accent-blue text-dark-bg font-semibold rounded-lg hover:shadow-lg hover:shadow-accent-cyan/50 transition-all"
            >
              Want to visualise the risk?
            </button>
          </div>
        )}

        {/* Risk Heatmap */}
        {analysis?.heatmap && showHeatmap && (
          <div className="mb-8">
            <RiskHeatmap 
              heatmap={analysis.heatmap}
              topRiskyCategory={analysis.top_risky_category}
            />
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contradictions (Main) */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">Detected Contradictions</h2>
            {contradictions.length === 0 ? (
              <div className="bg-dark-card border border-dark-border rounded-xl p-8 text-center">
                <p className="text-gray-400">
                  No contradictions detected. Your contracts appear consistent.
                </p>
              </div>
            ) : (
              contradictions.map((contradiction, idx) => (
                <ContradictionCard key={idx} contradiction={contradiction} />
              ))
            )}

            {/* Question & Answers Section */}
            <div className="mt-12 space-y-6">
              <h2 className="text-2xl font-bold text-white">Ask Questions</h2>
              <QuestionBox onSubmit={handleAskQuestion} isLoading={isAsking} />

              {/* Answer Cards */}
              {answers.length > 0 && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-100">Your Questions</h3>
                  {answers.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-dark-card border border-dark-border rounded-xl p-6"
                    >
                      <h4 className="font-semibold text-accent-cyan mb-3">{item.question}</h4>
                      <p className="text-gray-300 mb-4 leading-relaxed">{item.answer}</p>
                      {item.evidence && item.evidence.length > 0 && (
                        <div className="bg-dark-bg rounded-lg p-4 border border-dark-border mt-4">
                          <p className="text-sm font-medium text-gray-300 mb-3">Evidence:</p>
                          <ul className="space-y-2">
                            {item.evidence.map((ev, i) => (
                              <li key={i} className="text-sm text-gray-400">
                                📄 <strong>{ev.document}</strong> - Section {ev.section}: "{ev.text}"
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <ExportPanel onExport={handleExport} isLoading={isExporting} />

            {/* Analysis Info */}
            <div className="bg-dark-card border border-dark-border rounded-xl p-6 space-y-4">
              <h3 className="font-semibold text-gray-100">About This Analysis</h3>
              <div className="space-y-3 text-sm text-gray-400">
                <p>
                  ✓ Smart clause extraction preserves context
                </p>
                <p>
                  ✓ Cross-document contradiction detection
                </p>
                <p>
                  ✓ Risk assessment with Indian law context
                </p>
                <p>
                  ✓ Evidence traceability for all findings
                </p>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="bg-yellow-900/20 border border-yellow-600/50 rounded-xl p-4">
              <p className="text-xs text-yellow-100">
                <strong>Disclaimer:</strong> This analysis is for informational purposes only and does not constitute legal advice. Always consult with a qualified legal professional.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
