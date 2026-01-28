"""
PactLens Backend - In-Memory Vector Database
Simple embedding storage and similarity search
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity


class VectorDB:
    """Simple in-memory vector database for clause embeddings"""
    
    def __init__(self):
        self.clauses = []  # List of clause objects with embeddings
        self.embeddings = None  # NumPy array of embeddings

    def add_clause(
        self,
        clause_id: str,
        document_id: str,
        document_name: str,
        clause_type: str,
        section: str,
        title: str,
        text: str,
        embedding: List[float],
    ):
        """Add a clause with its embedding and metadata."""

        clause_record = {
            "id": clause_id,
            "document_id": document_id,
            "document_name": document_name,
            "clause_type": clause_type,
            "section": section,
            "title": title,
            "text": text,
            "embedding_index": len(self.clauses),
        }
        self.clauses.append(clause_record)

        # Update embeddings array
        if self.embeddings is None:
            self.embeddings = np.array([embedding])
        else:
            self.embeddings = np.vstack([self.embeddings, embedding])
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Find most similar clauses using cosine similarity
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of similar clauses with similarity scores
        """
        if self.embeddings is None or len(self.clauses) == 0:
            return []
        
        query = np.array([query_embedding])
        similarities = cosine_similarity(query, self.embeddings)[0]
        
        # Get top_k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Filter by minimum similarity
                results.append({
                    **self.clauses[int(idx)],
                    "similarity_score": float(similarities[idx]),
                })
        
        return results
    
    def search_filtered(
        self,
        query_embedding: List[float],
        clause_type: Optional[str] = None,
        exclude_document_id: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """Search with optional clause_type filter and document exclusion."""

        if self.embeddings is None or len(self.clauses) == 0:
            return []

        query = np.array([query_embedding])
        similarities = cosine_similarity(query, self.embeddings)[0]

        # Sort indices by similarity desc
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            clause = self.clauses[int(idx)]

            if exclude_document_id and clause.get("document_id") == exclude_document_id:
                continue

            if clause_type and clause.get("clause_type", "").lower() != clause_type.lower():
                continue

            score = float(similarities[idx])
            if score <= 0:
                continue

            results.append({**clause, "similarity_score": score})

            if len(results) >= top_k:
                break

        return results

    def search_by_type(self, clause_type: str) -> List[Dict]:
        """Find all clauses of a specific type"""
        return [c for c in self.clauses if c["clause_type"].lower() == clause_type.lower()]
    
    def get_all(self) -> List[Dict]:
        """Get all clauses"""
        return self.clauses
    
    def clear(self):
        """Clear all data"""
        self.clauses = []
        self.embeddings = None


# Global vector database instance
vector_db = VectorDB()
