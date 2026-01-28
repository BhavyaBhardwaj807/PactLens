"""
PactLens Backend - Core Models
Defines data structures for documents, clauses, and analysis
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    size: int
    pages: int = 0


class Clause(BaseModel):
    """Extracted clause/section from a document"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    document_name: str
    section_number: str
    clause_type: str  # e.g., "Confidentiality", "Termination", "IP Rights"
    title: str
    text: str
    embedding: Optional[List[float]] = None
    start_page: int = 0
    end_page: int = 0


class Contradiction(BaseModel):
    """Detected contradiction between clauses"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    clauses: List[Clause]
    risk_level: str  # "high", "medium", "low"
    risk_explanation: str
    indian_law_note: Optional[str] = None
    recommendations: List[str] = []
    confidence_score: float = 0.0


class QuestionAnswer(BaseModel):
    """Answer to a user question with evidence"""
    question: str
    answer: str
    evidence: List[Dict] = []
    confidence_score: float = 0.0


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    document_ids: List[str]
    total_documents: int
    total_clauses: int
    contradictions: List[Contradiction]
    timestamp: datetime = Field(default_factory=datetime.now)


class UploadResponse(BaseModel):
    """Response after document upload"""
    document_ids: List[str]
    filenames: List[str]
    total_size: int
