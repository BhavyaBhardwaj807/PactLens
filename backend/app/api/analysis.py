"""
PactLens Backend - Analysis API
Session-based analysis with isolated vector collections
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import uuid
import traceback
import os

from app.utils.vector_db import VectorDBClient
from app.rag.pipeline import RAGPipeline
from app.rag.llm_service import LLMService, EmbeddingsService
from app.utils.pdf_processor import PDFProcessor
from app.config import settings
from app.api.documents import uploaded_documents

router = APIRouter(prefix="/analysis", tags=["analysis"])

embeddings_service = EmbeddingsService(settings.gemini_api_key)
llm_service = LLMService(settings.gemini_api_key)
rag_pipeline = RAGPipeline(embeddings_service, llm_service)

analysis_cache = {}


class AnalyzeRequest(BaseModel):
    document_ids: List[str]


class QuestionRequest(BaseModel):
    question: str
    document_ids: List[str] = []


def cleanup_old_files(minutes=60):
    now = datetime.utcnow()
    to_delete = []

    for doc_id, doc in uploaded_documents.items():
        uploaded_at = doc.get("uploaded_at")
        if not uploaded_at:
            continue

        if now - uploaded_at > timedelta(minutes=minutes):
            path = doc.get("file_path")
            if path and os.path.exists(path):
                os.remove(path)
            to_delete.append(doc_id)

    for doc_id in to_delete:
        del uploaded_documents[doc_id]


def _build_vector_db_for_documents(document_ids: List[str], collection) -> None:
    """
    Populate the provided collection with embeddings for the given documents.
    Embeddings are added ONLY to this collection (session-scoped).
    """
    for doc_id in document_ids:
        if doc_id not in uploaded_documents:
            continue

        doc_metadata = uploaded_documents[doc_id]
        file_path = doc_metadata.get("file_path")
        if not file_path:
            continue

        text, _metadata = PDFProcessor.extract_text_and_metadata(file_path)
        clauses = PDFProcessor.chunk_by_sections(text)

        for idx, clause in enumerate(clauses):
            embedding = embeddings_service.embed_text(clause["text"])
            collection.add_clause(
                clause_id=f"{doc_id}_{idx}",
                document_id=doc_id,
                document_name=doc_metadata.get("filename", "Unknown"),
                clause_type=_detect_clause_type(clause),
                section=clause["section"],
                title=clause["title"],
                text=clause["text"],
                embedding=embedding,
            )


@router.post("/analyze")
async def analyze_documents(request: AnalyzeRequest):
    """
    Analyze uploaded documents for contradictions using a session-scoped collection.
    """
    cleanup_old_files(minutes=60)

    if not request.document_ids:
        raise HTTPException(400, "No documents provided")

    analysis_id = str(uuid.uuid4())
    collection_name = f"analysis_{analysis_id}"
    client = VectorDBClient()
    collection = None

    try:
        print(f"🧠 Creating collection: {collection_name}")
        collection = client.create_collection(name=collection_name)

        _build_vector_db_for_documents(request.document_ids, collection)

        all_clauses = collection.get_all()
        print(f"📦 Clause count in collection: {len(all_clauses)}")

        if not all_clauses:
            raise HTTPException(400, "No clauses extracted")

        contradictions = rag_pipeline.analyze_contradictions(all_clauses, collection)

        contradictions.sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(
                x.get("risk_level", "low"), 3
            )
        )

        result = {
            "document_ids": request.document_ids,
            "total_documents": len(set(c.get("document_id") for c in all_clauses)),
            "total_clauses": len(all_clauses),
            "contradictions": contradictions,
            "timestamp": datetime.now().isoformat(),
        }

        analysis_cache[str(request.document_ids)] = result
        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        if collection:
            print(f"🧹 Deleting collection: {collection_name}")
            client.delete_collection(name=collection_name)


@router.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Answer a question using a session-scoped collection.
    """
    cleanup_old_files(minutes=60)

    if not request.question.strip():
        raise HTTPException(400, "Question empty")

    doc_ids = request.document_ids or (
        list(analysis_cache.values())[-1]["document_ids"]
        if analysis_cache else []
    )

    if not doc_ids:
        raise HTTPException(400, "No documents available")

    analysis_id = str(uuid.uuid4())
    collection_name = f"analysis_{analysis_id}"
    client = VectorDBClient()
    collection = None

    try:
        print(f"🧠 Creating collection: {collection_name}")
        collection = client.create_collection(name=collection_name)

        _build_vector_db_for_documents(doc_ids, collection)

        if not collection.get_all():
            raise HTTPException(status_code=400, detail="No documents analyzed yet")

        answer = rag_pipeline.answer_question(request.question, collection)
        return answer

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, str(e))
    finally:
        if collection:
            print(f"🧹 Deleting collection: {collection_name}")
            client.delete_collection(name=collection_name)


def _detect_clause_type(clause: dict) -> str:
    text = (clause.get("title", "") + clause.get("text", "")).lower()

    if "confidential" in text:
        return "Confidentiality"
    if "termination" in text:
        return "Termination"
    if "intellectual" in text:
        return "IP Rights"
    if "salary" in text:
        return "Compensation"

    return "General"
