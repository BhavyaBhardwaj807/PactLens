import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const documentAPI = {
  // Upload documents
  upload: (formData) => {
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Get all uploaded documents
  list: () => api.get('/documents/list'),

  // Delete a document
  delete: (docId) => api.delete(`/documents/${docId}`),

  // Get document details
  get: (docId) => api.get(`/documents/${docId}`),
};

export const analysisAPI = {
  // Analyze uploaded documents
  analyze: (docIds) => api.post('/analysis/analyze', { document_ids: docIds }),

  // Get contradictions
  getContradictions: () => api.get('/analysis/contradictions'),

  // Get risk assessment
  getRisks: () => api.get('/analysis/risks'),

  // Ask question about documents
  askQuestion: (question) => api.post('/analysis/ask', { question }),

  // Export report
  exportReport: (format = 'pdf') => api.get(`/analysis/export?format=${format}`),
};

export default api;
