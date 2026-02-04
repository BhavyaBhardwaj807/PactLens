"""
PactLens Backend - Document Management API
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import uuid
from pathlib import Path
from datetime import datetime  # ✅ ADDED

from app.config import settings
from app.models.schemas import UploadResponse

router = APIRouter(prefix="/documents", tags=["documents"])

uploaded_documents = {}  # id -> metadata


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    document_ids = []
    filenames = []
    total_size = 0

    try:
        for file in files:

            if not file.filename.endswith('.pdf'):
                raise HTTPException(400, "Only PDF files allowed")

            doc_id = str(uuid.uuid4())
            file_path = os.path.join(settings.upload_dir, f"{doc_id}.pdf")

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # ✅ UPDATED METADATA
            uploaded_documents[doc_id] = {
                "id": doc_id,
                "filename": file.filename,
                "size": len(content),
                "file_path": file_path,
                "uploaded_at": datetime.utcnow(),  # ✅ NEW
            }

            document_ids.append(doc_id)
            filenames.append(file.filename)
            total_size += len(content)

    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

    return UploadResponse(
        document_ids=document_ids,
        filenames=filenames,
        total_size=total_size,
    )


@router.get("/list")
async def list_documents():
    return {
        "documents": [
            {
                "id": doc_id,
                "filename": doc["filename"],
                "size": doc["size"],
            }
            for doc_id, doc in uploaded_documents.items()
        ]
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str):

    if document_id not in uploaded_documents:
        raise HTTPException(404, "Document not found")

    doc = uploaded_documents[document_id]

    path = doc.get("file_path")
    if path and os.path.exists(path):
        os.remove(path)

    del uploaded_documents[document_id]

    return {"message": "Document deleted"}
