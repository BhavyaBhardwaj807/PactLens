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
from app.utils.risk import generate_risk_heatmap, compute_overall_risk
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


def _calculate_risk_score(contradictions, total_clauses):
    """
    Calculate overall contract risk score (0-10) using legal AI methodology.
    Combines: Severity × Frequency × Clause Importance × Confidence
    """
    if not contradictions:
        return {"score": 0, "level": "Low", "summary": "No significant risks detected"}
    
    # Step 1: Assign weights
    RISK_WEIGHTS = {
        "high": 3.0,
        "medium": 2.0,
        "low": 1.0
    }
    
    # Clause importance weights (legal priority)
    IMPORTANCE_WEIGHTS = {
        "Compensation": 1.5,
        "Confidentiality": 1.3,
        "Termination": 1.4,
        "Liability": 1.6,
        "Notice Period": 1.2,
        "Jurisdiction": 1.1,
        "Contract Terms": 1.0
    }
    
    # Step 2: Score each conflict
    total_score = 0.0
    max_possible_score = 0.0
    
    for c in contradictions:
        risk_level = c.get("risk_level", "low")
        clause_type = c.get("clause_type_display", "Contract Terms")
        confidence = c.get("confidence_score", 0.8)
        conflict_count = c.get("conflict_count", 1)
        
        risk_weight = RISK_WEIGHTS.get(risk_level, 1.0)
        importance_weight = IMPORTANCE_WEIGHTS.get(clause_type, 1.0)
        
        # Calculate conflict score
        conflict_score = risk_weight * importance_weight * confidence * conflict_count
        total_score += conflict_score
        
        # Maximum possible (if all were high risk, high importance)
        max_possible_score += 3.0 * 1.6 * 1.0 * conflict_count
    
    # Step 3 & 4: Normalize to /10 scale
    if max_possible_score > 0:
        normalized_score = (total_score / max_possible_score) * 10
    else:
        normalized_score = 0
    
    score = round(min(normalized_score, 10.0), 1)
    
    # Determine level and summary
    if score >= 7.0:
        level = "High"
        summary = "Significant contract risks detected. Legal review strongly recommended."
    elif score >= 4.0:
        level = "Medium"
        summary = "Moderate contract risks detected. Review recommended before execution."
    else:
        level = "Low"
        summary = "Minor inconsistencies detected. Review for completeness."
    
    return {
        "score": score,
        "level": level,
        "summary": summary,
        "total_conflicts": sum(c.get("conflict_count", 1) for c in contradictions)
    }


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
        
        print(f"\n🚀 RAG Pipeline returned {len(contradictions)} contradictions")
        if contradictions:
            print(f"First contradiction: {contradictions[0].get('title', 'No title')}")

        # Don't re-sort here - pipeline already sorted by risk/priority/confidence
        
        # Generate risk heatmap
        heatmap_data = generate_risk_heatmap(contradictions)
        
        # Calculate overall risk score
        overall_risk = compute_overall_risk(heatmap_data.get("heatmap", []))

        result = {
            "document_ids": request.document_ids,
            "total_documents": len(set(c.get("document_id") for c in all_clauses)),
            "total_clauses": len(all_clauses),
            "contradictions": contradictions,
            "risk_score": overall_risk["overall_score"],
            "risk_level": overall_risk["overall_level"],
            "risk_summary": overall_risk["summary"],
            "heatmap": heatmap_data["heatmap"],
            "top_risky_category": heatmap_data["top_risky_category"],
            "timestamp": datetime.now().isoformat(),
        }
        
        print(f"\n📤 API RETURNING: {len(result['contradictions'])} contradictions")
        print(f"📊 OVERALL RISK: {overall_risk['overall_score']}/10 ({overall_risk['overall_level']})")
        print(f"📈 HEATMAP: {heatmap_data['top_risky_category']}")
        print(f"RESULT KEYS: {result.keys()}\n")

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
        raise HTTPException(400, "Question cannot be empty")

    # Get document IDs from request or from last analysis
    doc_ids = request.document_ids
    if not doc_ids and analysis_cache:
        try:
            doc_ids = list(analysis_cache.values())[-1]["document_ids"]
            print(f"📋 Using document_ids from cache: {doc_ids}")
        except (IndexError, KeyError):
            doc_ids = []
    
    if not doc_ids:
        print(f"❌ No document_ids provided and cache is empty")
        raise HTTPException(400, "No documents available. Please analyze documents first.")

    analysis_id = str(uuid.uuid4())
    collection_name = f"analysis_{analysis_id}"
    client = VectorDBClient()
    collection = None

    try:
        print(f"🧠 Creating collection: {collection_name}")
        collection = client.create_collection(name=collection_name)

        _build_vector_db_for_documents(doc_ids, collection)
        
        all_clauses = collection.get_all()
        print(f"📦 Clauses in collection: {len(all_clauses)}")

        if not all_clauses:
            raise HTTPException(status_code=400, detail="No clauses extracted from documents")

        print(f"❓ Answering question: {request.question[:100]}...")
        answer = rag_pipeline.answer_question(request.question, collection)
        print(f"✅ Answer generated: {answer.get('answer', '')[:100]}...")
        return answer

    except HTTPException:
        raise
    except Exception as e:
        print(f"🔴 Error in ask_question: {str(e)}")
        traceback.print_exc()
        raise HTTPException(500, f"Failed to answer question: {str(e)}")
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
