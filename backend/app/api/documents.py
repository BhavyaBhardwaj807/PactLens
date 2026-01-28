"""
PactLens Backend - Document Management API
Endpoints for uploading and managing contract documents
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import uuid
from pathlib import Path

from app.config import settings
from app.models.schemas import UploadResponse, DocumentMetadata
from app.utils.pdf_processor import PDFProcessor
from app.utils.vector_db import vector_db
from app.rag.llm_service import EmbeddingsService

# Initialize router
router = APIRouter(prefix="/documents", tags=["documents"])

# Track uploaded documents
uploaded_documents = {}  # id -> metadata


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload contract documents
    
    Args:
        files: List of PDF files
        
    Returns:
        Upload response with document IDs
    """
    
    # Create upload directory if it doesn't exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    
    document_ids = []
    filenames = []
    total_size = 0
    
    # Initialize embeddings service
    embeddings_service = EmbeddingsService(settings.gemini_api_key)
    
    try:
        for file in files:
            # Validate file
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files allowed")
            
            if file.size > settings.max_upload_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size: {settings.max_upload_size / 1024 / 1024}MB"
                )
            
            # Save file
            doc_id = str(uuid.uuid4())
            file_path = os.path.join(settings.upload_dir, f"{doc_id}.pdf")
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Extract text and metadata
            text, metadata = PDFProcessor.extract_text_and_metadata(file_path)
            
            # Extract clauses
            clauses = PDFProcessor.chunk_by_sections(text)
            
            # Generate embeddings and add to vector DB
            for idx, clause in enumerate(clauses):
                clause_id = f"{doc_id}_clause_{idx}"
                embedding = embeddings_service.embed_text(clause["text"])
                
                vector_db.add_clause(
                    clause_id=clause_id,
                    document_id=doc_id,
                    document_name=file.filename,
                    clause_type=_detect_clause_type(clause),
                    section=clause["section"],
                    title=clause["title"],
                    text=clause["text"],
                    embedding=embedding,
                )
            
            # Store document metadata
            doc_metadata = DocumentMetadata(
                id=doc_id,
                filename=file.filename,
                size=file.size,
                pages=metadata.get("pages", 0),
            )
            uploaded_documents[doc_id] = doc_metadata
            
            document_ids.append(doc_id)
            filenames.append(file.filename)
            total_size += file.size
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    return UploadResponse(
        document_ids=document_ids,
        filenames=filenames,
        total_size=total_size,
    )


@router.get("/list")
async def list_documents():
    """Get list of uploaded documents"""
    return {
        "documents": [
            {
                "id": doc_id,
                "filename": doc.filename,
                "size": doc.size,
                "pages": doc.pages,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
            for doc_id, doc in uploaded_documents.items()
        ]
    }


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get specific document details"""
    if document_id not in uploaded_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = uploaded_documents[document_id]
    return {
        "id": document_id,
        "filename": doc.filename,
        "size": doc.size,
        "pages": doc.pages,
        "uploaded_at": doc.uploaded_at.isoformat(),
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in uploaded_documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    file_path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from tracking
    del uploaded_documents[document_id]
    
    return {"message": "Document deleted"}


def _detect_clause_type(clause: dict) -> str:
    """
    Simple heuristic to detect clause type from title
    In production, use ML classification
    """
    title = clause.get("title", "").lower()
    text = clause.get("text", "").lower()[:200]
    
    keywords = {
        "Confidentiality": ["confidential", "secret", "nda", "disclosure"],
        "Termination": ["termination", "end", "terminate", "resign"],
        "IP Rights": ["intellectual property", "copyright", "patent", "rights"],
        "Compensation": ["salary", "payment", "compensation", "pay"],
        "Non-Compete": ["non-compete", "non compete", "compete"],
        "Work Hours": ["hours", "work", "schedule", "timing"],
        "Benefits": ["benefit", "insurance", "health", "pension"],
        "Dispute": ["dispute", "legal", "arbitration", "jurisdiction"],
    }
    
    combined_text = title + " " + text
    
    for clause_type, keywords_list in keywords.items():
        if any(kw in combined_text for kw in keywords_list):
            return clause_type
    
    return "General"
