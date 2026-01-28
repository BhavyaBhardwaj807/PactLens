import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DocumentUploader from '../components/DocumentUploader';
import { Loader, CheckCircle } from 'lucide-react';
import { documentAPI, analysisAPI } from '../utils/api';

export default function UploadPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const handleDrop = (acceptedFiles) => {
    const newDocs = acceptedFiles.map(file => ({
      name: file.name,
      size: file.size,
      file: file,
    }));
    setDocuments([...documents, ...newDocs]);
    setError('');
  };

  const handleRemove = (idx) => {
    setDocuments(documents.filter((_, i) => i !== idx));
  };

  const handleAnalyze = async () => {
    if (documents.length === 0) {
      setError('Please upload at least one document');
      return;
    }

    setIsAnalyzing(true);
    setError('');

    try {
      // Upload documents
      const formData = new FormData();
      documents.forEach(doc => {
        formData.append('files', doc.file);
      });

      const uploadResponse = await documentAPI.upload(formData);
      const docIds = uploadResponse.data.document_ids;

      // Analyze
      const analysisResponse = await analysisAPI.analyze(docIds);

      // Navigate to results
      navigate('/results', {
        state: {
          analysis: analysisResponse.data,
          docIds,
        },
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred during analysis');
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-dark pt-20">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-white mb-4">Analyze Your Contracts</h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Upload your legal documents and let PactLens detect contradictions and risks across all files.
          </p>
        </div>

        {/* Upload Area */}
        <DocumentUploader
          documents={documents}
          onDrop={handleDrop}
          onRemove={handleRemove}
        />

        {/* Error Message */}
        {error && (
          <div className="mt-6 bg-risk-high/10 border border-risk-high/50 rounded-lg p-4 text-risk-high">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 justify-center">
          <button
            onClick={handleAnalyze}
            disabled={documents.length === 0 || isAnalyzing}
            className="flex items-center gap-2 btn-primary text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <Loader size={20} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <CheckCircle size={20} />
                Analyze Documents
              </>
            )}
          </button>
        </div>

        {/* Info Box */}
        <div className="mt-12 bg-accent-cyan/5 border border-accent-cyan/30 rounded-xl p-6 text-center">
          <h3 className="font-semibold text-accent-cyan mb-2">Supported Formats</h3>
          <p className="text-gray-400 text-sm">
            PDF files (Offer Letters, NDAs, Employment Contracts, Company Policies, etc.)
          </p>
          <p className="text-gray-500 text-xs mt-4">
            📋 Your documents are processed securely and not stored permanently.
          </p>
        </div>
      </div>
    </div>
  );
}
