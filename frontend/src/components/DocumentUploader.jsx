import React from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

export default function DocumentUploader({ documents, onDrop, onRemove }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6 pt-16">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ${
          isDragActive
            ? 'border-accent-cyan bg-accent-cyan/10 shadow-accent'
            : 'border-dark-border hover:border-accent-cyan bg-dark-card/50'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex justify-center mb-4">
          <Upload size={48} className="text-accent-cyan" />
        </div>
        <h3 className="text-lg font-semibold text-gray-100 mb-2">
          {isDragActive ? 'Drop your contracts here' : 'Upload Legal Contracts'}
        </h3>
        <p className="text-gray-400 mb-4">
          Drag & drop PDFs or click to select files
        </p>
        <p className="text-sm text-gray-500">
          Supported: PDF files (Offer Letters, NDAs, Employment Contracts, etc.)
        </p>
      </div>

      {/* Document List */}
      {documents.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-100">Uploaded Documents ({documents.length})</h3>
          <div className="grid gap-3">
            {documents.map((doc, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-dark-card border border-dark-border rounded-lg p-4 hover:border-accent-cyan/50 transition-all"
              >
                <div className="flex items-center gap-3 flex-1">
                  <FileText size={24} className="text-accent-cyan" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-100 truncate">{doc.name}</p>
                    <p className="text-sm text-gray-400">{formatFileSize(doc.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => onRemove(idx)}
                  className="p-2 hover:bg-dark-border rounded-lg transition-colors ml-2"
                  title="Remove file"
                >
                  <X size={20} className="text-gray-400 hover:text-risk-high" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
