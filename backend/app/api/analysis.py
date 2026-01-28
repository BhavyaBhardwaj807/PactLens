"""
PactLens Backend - Analysis API
Endpoints for contract analysis, contradiction detection, and Q&A
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
import json
from datetime import datetime

from app.models.schemas import Contradiction, QuestionAnswer
from app.utils.vector_db import vector_db
from app.rag.pipeline import RAGPipeline
from app.rag.llm_service import LLMService, EmbeddingsService
from app.config import settings

# Initialize router
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Initialize services
embeddings_service = EmbeddingsService(settings.gemini_api_key)
llm_service = LLMService(settings.gemini_api_key)
rag_pipeline = RAGPipeline(embeddings_service, llm_service, vector_db)

# Store analysis results in memory
analysis_cache = {}


class AnalyzeRequest(BaseModel):
    document_ids: List[str]


class QuestionRequest(BaseModel):
    question: str


@router.post("/analyze")
async def analyze_documents(request: AnalyzeRequest):
    """
    Analyze uploaded documents for contradictions
    
    Args:
        request: Analysis request with document IDs
        
    Returns:
        Analysis results
    """
    
    if not request.document_ids:
        raise HTTPException(status_code=400, detail="No documents provided")
    
    try:
        # Get all clauses from vector DB
        all_clauses = vector_db.get_all()
        
        if not all_clauses:
            raise HTTPException(status_code=400, detail="No clauses extracted from documents")
        
        # Detect contradictions
        contradictions = rag_pipeline.analyze_contradictions(all_clauses)
        
        # Sort by risk level
        risk_order = {"high": 0, "medium": 1, "low": 2}
        contradictions.sort(
            key=lambda x: risk_order.get(x.get("risk_level", "low"), 3)
        )
        
        result = {
            "document_ids": request.document_ids,
            "total_documents": len(set(c.get("document_id") for c in all_clauses)),
            "total_clauses": len(all_clauses),
            "contradictions": contradictions,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Cache result
        analysis_cache[str(request.document_ids)] = result
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/contradictions")
async def get_contradictions():
    """Get cached contradictions"""
    if not analysis_cache:
        raise HTTPException(status_code=404, detail="No analysis available")
    
    # Return latest analysis
    latest = list(analysis_cache.values())[-1]
    return {"contradictions": latest.get("contradictions", [])}


@router.get("/risks")
async def get_risks():
    """Get risk assessment summary"""
    if not analysis_cache:
        raise HTTPException(status_code=404, detail="No analysis available")
    
    latest = list(analysis_cache.values())[-1]
    contradictions = latest.get("contradictions", [])
    
    return {
        "high_risk": [c for c in contradictions if c.get("risk_level") == "high"],
        "medium_risk": [c for c in contradictions if c.get("risk_level") == "medium"],
        "low_risk": [c for c in contradictions if c.get("risk_level") == "low"],
        "total": len(contradictions),
    }


@router.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a question about the contracts
    
    Args:
        request: Question request
        
    Returns:
        Answer with evidence
    """
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not vector_db.get_all():
        raise HTTPException(status_code=400, detail="No documents analyzed yet")
    
    try:
        answer = rag_pipeline.answer_question(request.question)
        return answer
    except Exception as e:
        print(f"Question answering error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@router.get("/export")
async def export_report(format: str = "pdf"):
    """
    Export analysis report
    
    Args:
        format: Output format (pdf or json)
        
    Returns:
        Report in requested format
    """
    
    if not analysis_cache:
        raise HTTPException(status_code=404, detail="No analysis available")
    
    latest = list(analysis_cache.values())[-1]
    
    if format == "json":
        return latest
    
    elif format == "pdf":
        # In production, use a library like reportlab or weasyprint
        # For now, return JSON that frontend can convert
        report_content = _generate_pdf_content(latest)
        return report_content
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


def _generate_pdf_content(analysis_result: dict) -> dict:
    """Generate PDF-ready content"""
    
    contradictions = analysis_result.get("contradictions", [])
    
    # Create structured report
    report = {
        "title": "PactLens Analysis Report",
        "generated_at": analysis_result.get("timestamp"),
        "summary": {
            "total_documents": analysis_result.get("total_documents"),
            "total_clauses": analysis_result.get("total_clauses"),
            "total_contradictions": len(contradictions),
        },
        "contradictions": contradictions,
        "disclaimer": "This report is for informational purposes only and does not constitute legal advice.",
    }
    
    return report
