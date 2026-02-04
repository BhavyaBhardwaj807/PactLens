# RAG Pipeline Refactoring: Per-Analysis FAISS Implementation

## Overview
The RAG pipeline has been refactored to use **per-analysis vector databases** instead of a global, persistent FAISS store. This ensures PactLens remains stateless, privacy-safe, and memory-efficient.

## Key Changes

### 1. **VectorDB Class** (`backend/app/utils/vector_db.py`)
- **Removed**: Global `vector_db` instance at module level
- **Removed**: Persistence to disk
- **Added**: Destructor (`__del__`) for explicit cleanup on garbage collection
- **Result**: VectorDB instances are now created fresh for each analysis and automatically cleaned up

**Architecture:**
```python
# Before: Global state
vector_db = VectorDB()  # Created once, persists forever

# After: Per-analysis instances
vector_db = VectorDB()  # Created per-analysis, cleaned up automatically
```

### 2. **RAGPipeline Class** (`backend/app/rag/pipeline.py`)
- **Removed**: Stored reference to global `vector_db`
- **Updated**: `__init__()` no longer accepts `vector_db` parameter
- **Updated**: `analyze_contradictions(clauses, vector_db)` - now accepts `vector_db` as parameter
- **Updated**: `answer_question(question, vector_db)` - now accepts `vector_db` as parameter
- **Result**: Pipeline is stateless and works with session-specific indexes

**Method signatures:**
```python
# Before
def analyze_contradictions(self, clauses: List[Dict]) -> List[Dict]:
    # Used self.vector_db (global state)

# After
def analyze_contradictions(self, clauses: List[Dict], vector_db) -> List[Dict]:
    # Uses passed vector_db instance
```

### 3. **Analysis API** (`backend/app/api/analysis.py`)
- **Added**: `_build_vector_db_for_documents(document_ids)` function
  - Reads uploaded PDF files
  - Extracts clauses
  - Generates embeddings
  - Populates fresh VectorDB instance
  - Returns populated instance for analysis

- **Updated**: `/analyze` endpoint
  - Creates per-analysis vector DB
  - Populates from uploaded documents
  - Runs contradiction detection
  - Returns results
  - Vector DB goes out of scope → automatic garbage collection

- **Updated**: `/ask` endpoint (Q&A)
  - Creates per-analysis vector DB from specified documents
  - Answers question using session-scoped index
  - Returns answer with evidence
  - Vector DB garbage collected after response

- **Added**: `_detect_clause_type()` function (moved from documents.py)

**Per-analysis flow:**
```
1. Client requests /analyze with document_ids
2. API creates fresh VectorDB()
3. Loads PDF files from disk
4. Extracts clauses → generates embeddings
5. Adds to VectorDB instance
6. Runs RAG pipeline with session vector_db
7. Returns results
8. VectorDB reference drops → garbage collection
9. No state persists to next analysis
```

### 4. **Documents API** (`backend/app/api/documents.py`)
- **Removed**: Import of global `vector_db`
- **Removed**: Import of `EmbeddingsService`, `PDFProcessor`, `_detect_clause_type`
- **Updated**: `/upload` endpoint
  - Only validates and saves PDF files
  - Stores metadata (filename, size, file_path)
  - **Does NOT** extract clauses or generate embeddings
  - Embeddings are created on-demand during analysis
  
- **Updated**: `/list` and `/{document_id}` endpoints
  - Work with simple metadata dicts (not DocumentMetadata objects)

- **Removed**: `_detect_clause_type()` function (moved to analysis.py)

**Stateless upload process:**
```
1. Client uploads PDFs
2. API validates and saves to disk
3. Stores metadata only: {id, filename, size, file_path}
4. Returns document_ids
5. No embeddings created
6. No global state modified
```

## Benefits

### 1. **Privacy & Data Safety**
- ✅ No persistent embeddings on disk
- ✅ Embeddings exist only during analysis
- ✅ No data leakage between analyses
- ✅ Automatic cleanup via Python garbage collection

### 2. **Memory Efficiency**
- ✅ Vector DB only allocated during analysis
- ✅ Freed immediately after analysis completes
- ✅ Multiple analyses don't accumulate memory
- ✅ Scalable to many concurrent requests

### 3. **Stateless Operation**
- ✅ No global state to manage
- ✅ Each analysis is independent
- ✅ No initialization/teardown complexity
- ✅ Simpler deployment and scaling

### 4. **Security**
- ✅ No permanent vector index to secure
- ✅ No database migrations needed
- ✅ Reduced attack surface
- ✅ GDPR/privacy-friendly design

## Implementation Details

### Vector DB Lifecycle

**Per-Analysis Process:**
```python
# 1. Create fresh instance
vector_db = VectorDB()  # Empty, no state

# 2. Populate from documents
for doc_id in request.document_ids:
    # Load PDF
    # Extract clauses
    # Generate embeddings
    vector_db.add_clause(...)

# 3. Run analysis
contradictions = rag_pipeline.analyze_contradictions(clauses, vector_db)

# 4. Return results
return result

# 5. Automatic cleanup
# vector_db goes out of scope
# Python garbage collection runs
# __del__() method clears data
```

### Embeddings Generation
- **When**: Only during analysis, never during upload
- **Where**: In `_build_vector_db_for_documents()` 
- **How**: Generated in-memory, added to VectorDB, never persisted to disk
- **Lifecycle**: Exists only for duration of analysis request

### API Changes for Clients

**Upload endpoint** (unchanged from client perspective):
```
POST /api/documents/upload
- Send PDFs
- Receive document_ids
- Documents stored, ready for analysis
```

**Analysis endpoint** (NEW - requires document_ids):
```
POST /api/analysis/analyze
{
  "document_ids": ["doc1", "doc2"]
}
- Analyze specific documents
- Fresh vector DB created
- Contradictions detected
- Results returned
- Vector DB cleaned up
```

**Q&A endpoint** (UPDATED - now requires document_ids):
```
POST /api/analysis/ask
{
  "question": "What is the termination clause?",
  "document_ids": ["doc1", "doc2"]
}
- Answer question about specific documents
- Fresh vector DB created
- Evidence from documents
- Results returned
- Vector DB cleaned up
```

## File Structure Changes

### Modified Files:
1. `backend/app/utils/vector_db.py` - Removed global instance
2. `backend/app/rag/pipeline.py` - Removed global vector_db dependency
3. `backend/app/api/analysis.py` - Added per-analysis vector DB creation
4. `backend/app/api/documents.py` - Removed embedding generation

### No Changes Needed:
- `backend/app/main.py` - Already imports only routers
- `backend/app/rag/llm_service.py` - Independent of vector_db
- `backend/app/utils/pdf_processor.py` - Independent of vector_db
- Frontend code - API contracts unchanged

## Testing Recommendations

1. **Unit Tests**
   - Verify VectorDB creation/cleanup
   - Test garbage collection with destructor
   - Verify per-analysis isolation

2. **Integration Tests**
   - Upload documents → Analyze → Verify no state leaks
   - Multiple concurrent analyses → Verify isolation
   - Q&A with fresh vector DB → Verify functionality

3. **Memory Tests**
   - Monitor memory during multiple analyses
   - Verify cleanup after analysis completion
   - Test with large documents

4. **Privacy Tests**
   - Verify no embeddings on disk
   - Check filesystem for vector DB files
   - Verify cleanup in all exception paths

## Migration Notes

### For Frontend/Clients:
- **Q&A endpoint** now requires `document_ids` field
- Update request payloads accordingly
- No other API changes needed

### For Developers:
- Don't import `vector_db` from `app.utils.vector_db`
- Pass `vector_db` as parameter to pipeline methods
- Always create VectorDB instance per analysis

### Performance Considerations:
- Per-analysis embedding generation adds latency (unavoidable for privacy)
- Cache frequent questions at application level if needed
- Consider batch processing for multiple analyses

## Future Improvements

1. **Caching Layer**: Add request-level caching for identical analyses
2. **Vector DB Pooling**: Reuse VectorDB instances within time window
3. **Async Embedding**: Generate embeddings concurrently
4. **Incremental Updates**: Support adding documents to existing analysis
5. **FAISS Optimization**: Use exact FAISS library instead of sklearn for performance

## Conclusion

This refactoring achieves the requirements:
- ✅ **No global FAISS store** - Removed completely
- ✅ **Per-analysis instantiation** - Created fresh for each request
- ✅ **Current documents only** - Populated from specified document_ids
- ✅ **Automatic cleanup** - Via Python garbage collection
- ✅ **No disk persistence** - Embeddings never written to storage
- ✅ **Stateless, privacy-safe, memory-efficient** - Architectural improvements
