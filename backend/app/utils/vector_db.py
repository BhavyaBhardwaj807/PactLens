"""
PactLens Backend - In-Memory Vector Database
Simple embedding storage and similarity search
Per-analysis instance (no global persistence)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity


class VectorDB:
    """
    In-memory vector database for clause embeddings.
    
    Instantiated per-analysis to ensure:
    - No global state
    - Automatic garbage collection after use
    - Privacy and memory efficiency
    - Stateless operation
    """
    
    def __init__(self):
        """Initialize empty in-memory vector database."""
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
    ) -> None:
        """
        Add a clause with its embedding and metadata.
        
        Args:
            clause_id: Unique identifier for the clause
            document_id: Document containing the clause
            document_name: Human-readable document name
            clause_type: Category/type of clause
            section: Section reference
            title: Clause title
            text: Full clause text
            embedding: Embedding vector (list of floats)
        """

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
        min_similarity: float = 0.0,
    ) -> List[Dict]:
        """
        Search with filters and optimizations.
        
        Args:
            query_embedding: Query vector
            clause_type: Only return clauses of this type
            exclude_document_id: Skip clauses from this document
            top_k: Maximum results to return
            min_similarity: Minimum similarity threshold (0.0-1.0)
            
        Returns:
            List of matching clauses with similarity scores
        """

        if self.embeddings is None or len(self.clauses) == 0:
            return []

        query = np.array([query_embedding])
        similarities = cosine_similarity(query, self.embeddings)[0]

        # Sort indices by similarity descending
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            clause = self.clauses[int(idx)]
            score = float(similarities[idx])

            # Apply filters
            if score < min_similarity:
                break  # Early stopping (list is sorted)

            if exclude_document_id and clause.get("document_id") == exclude_document_id:
                continue

            if clause_type and clause.get("clause_type", "").lower() != clause_type.lower():
                continue

            results.append({**clause, "similarity_score": score})

            if len(results) >= top_k:
                break

        return results

    def query(
        self,
        query_embedding: List[float],
        clause_type: Optional[str] = None,
        exclude_document_id: Optional[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> List[Dict]:
        """
        Collection-style query wrapper.
        Use this to align with collection.query(...) semantics.
        """
        return self.search_filtered(
            query_embedding,
            clause_type=clause_type,
            exclude_document_id=exclude_document_id,
            top_k=top_k,
            min_similarity=min_similarity,
        )

    def search_by_type(self, clause_type: str) -> List[Dict]:
        """Find all clauses of a specific type"""
        return [c for c in self.clauses if c["clause_type"].lower() == clause_type.lower()]
    
    def get_all(self) -> List[Dict]:
        """Get all clauses"""
        return self.clauses
    
    def clear(self) -> None:
        """Clear all data (prepare for garbage collection)"""
        self.clauses = []
        self.embeddings = None
    
    def __del__(self):
        """Destructor to ensure cleanup on garbage collection"""
        self.clear()


class VectorDBClient:
    """
    In-memory collection manager for session-based vector stores.

    Each collection is a separate VectorDB instance.
    Used to isolate embeddings per analysis run.
    """

    def __init__(self):
        self._collections: Dict[str, VectorDB] = {}

    def create_collection(self, name: str) -> VectorDB:
        """Create a new collection with the given name."""
        if name in self._collections:
            raise ValueError(f"Collection already exists: {name}")
        collection = VectorDB()
        self._collections[name] = collection
        return collection

    def get_collection(self, name: str) -> VectorDB | None:
        """Return a collection by name if it exists."""
        return self._collections.get(name)

    def delete_collection(self, name: str) -> None:
        """Delete a collection and free its memory."""
        collection = self._collections.pop(name, None)
        if collection:
            collection.clear()
