# PactLens - Legal Contract Analysis Platform

An intelligent web application that analyzes multiple legal contracts simultaneously to detect contradictions, conflicts, and hidden risks with a focus on Indian legal context.

**Status**: ✅ MVP Complete | 45+ Files | 4700+ Lines of Code | Fully Documented

## 🎯 Features

- **Multi-document Upload**: Upload multiple PDFs at once (contracts, offers, NDAs, policies)
- **Smart Clause Extraction**: Intelligent parsing that preserves clause context and relationships
- **Cross-Contract Analysis**: Detect contradictions and conflicts across different documents
- **Risk Categorization**: High/Medium/Low risk levels with plain-English explanations
- **Question-Driven Analysis**: Ask questions about your contracts and get instant answers
- **Evidence Traceability**: Every finding cites the source document and clause
- **Indian Law Context**: Considers enforceability under Indian legal norms
- **Export Reports**: Download detailed PDF reports

## 📂 Project Structure

```
PactLens/
├── frontend/                          # React + Tailwind CSS
│   ├── src/
│   │   ├── components/               # 7 Reusable components
│   │   ├── pages/                    # 3 Page-level components
│   │   ├── utils/api.js              # API client
│   │   ├── styles/globals.css        # Dark theme styles
│   │   ├── App.jsx & main.jsx
│   ├── package.json, vite.config.js, tailwind.config.js
│
├── backend/                           # FastAPI + Python + RAG
│   ├── app/
│   │   ├── api/                      # 2 Route modules
│   │   │   ├── documents.py          # Upload & management
│   │   │   └── analysis.py           # Analysis & Q&A
│   │   ├── rag/                      # RAG Pipeline
│   │   │   ├── pipeline.py           # Contradiction detection
│   │   │   └── llm_service.py        # Google Gemini integration
│   │   ├── models/schemas.py         # Data models
│   │   ├── utils/                    # PDF & Vector DB
│   │   │   ├── pdf_processor.py      # PDF extraction
│   │   │   └── vector_db.py          # In-memory vector store
│   │   ├── main.py & config.py
│   ├── venv/                         # Virtual environment
│   ├── requirements.txt
│   ├── setup.bat
│   └── data/                         # Uploaded PDFs
│
├── setup.sh & setup.bat              # Automated setup scripts
└── README.md
```

**See [FILE_INDEX.md](./FILE_INDEX.md) for complete file listing**

## � Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Gemini API key (optional: works with mock data without key)

### Windows Setup (Easiest)

```bash
# Run setup script
setup.bat

# Then:
# Terminal 1 - Backend:
cd backend
python -m venv venv
venv\Scripts\activate
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend:
cd frontend
npm run dev

# Open browser to http://localhost:5173
```

### Linux/macOS Setup

```bash
# Run setup script
./setup.sh

# Then follow same instructions as Windows
```

### Manual Setup

See [SETUP.md](./SETUP.md) for detailed step-by-step instructions.

## 📋 API Endpoints (10 Total)

**Health & Info**
- `GET /` - API info
- `GET /health` - Health check

**Documents**
- `POST /api/documents/upload` - Upload PDF contracts
- `GET /api/documents/list` - List uploaded documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

**Analysis**
- `POST /api/analysis/analyze` - Analyze documents for contradictions
- `GET /api/analysis/contradictions` - Get detected contradictions
- `GET /api/analysis/risks` - Get risk assessment
- `POST /api/analysis/ask` - Ask questions about contracts
- `GET /api/analysis/export?format=pdf|json` - Export report

Interactive docs: **http://localhost:8000/docs**

## 🎨 UI/UX

**Dark Theme Design**
- Background: Near-black (#0B0F1A)
- Primary Accent: Bluish-cyan gradient (#006FFF → #00D9FF)
- Risk Colors:
  - High Risk: Red (#EF4444)
  - Medium Risk: Amber (#F59E0B)
  - Low Risk: Blue (#60A5FA)

**Pages**
1. **Landing Page** - Product overview and CTA
2. **Upload Page** - Drag-drop document upload
3. **Results Page** - Contradiction analysis and Q&A

## � Documentation

| Document | Purpose |
|----------|---------|
| [SETUP.md](./SETUP.md) | Step-by-step installation (Windows/Linux/macOS) |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System architecture & technical details |
| [USAGE.md](./USAGE.md) | User guide with feature explanations |
| [QUICK_REF.md](./QUICK_REF.md) | Quick reference & common commands |
| [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) | Completion checklist & next steps |
| [FILE_INDEX.md](./FILE_INDEX.md) | Complete file structure & index |

**Start here**: [SETUP.md](./SETUP.md)

## ⚠️ Disclaimer

PactLens is for **informational purposes only** and does NOT provide legal advice. Always consult with a qualified legal professional before making decisions based on contract analysis.

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for startups and legal professionals**
