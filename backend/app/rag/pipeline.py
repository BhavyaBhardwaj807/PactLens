"""
PactLens Backend - RAG (Retrieval Augmented Generation) Pipeline
Handles embeddings, similarity search, and AI-powered analysis
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from json import JSONDecodeError


logger = logging.getLogger(__name__)


class RAGPipeline:
    """Main RAG pipeline for contract analysis"""
    
    def __init__(self, embeddings_service, llm_service, vector_db):
        """
        Initialize RAG pipeline
        
        Args:
            embeddings_service: Service for generating embeddings
            llm_service: LLM service for analysis
            vector_db: Vector database for similarity search
        """
        self.embeddings = embeddings_service
        self.llm = llm_service
        self.vector_db = vector_db
        self.metrics = {
            "clauses_processed": 0,
            "vector_searches": 0,
            "llm_calls": 0,
        }
    
    def analyze_contradictions(self, clauses: List[Dict]) -> List[Dict]:
        """
        Detect contradictions between clauses across documents
        
        Args:
            clauses: List of extracted clauses
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        seen_pairs = set()
        vector_searches = 0
        llm_calls = 0

        for clause in clauses:
            clause_type = clause.get("clause_type", "unknown")
            clause_doc = clause.get("document_id")

            query_embedding = self._get_clause_embedding(clause)
            similar_clauses = self.vector_db.search_filtered(
                query_embedding,
                clause_type=clause_type,
                exclude_document_id=clause_doc,
                top_k=5,
            )
            vector_searches += 1

            for candidate in similar_clauses:
                pair_key = tuple(sorted([clause.get("id"), candidate.get("id")]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                llm_calls += 1
                contradiction = self._detect_contradiction(
                    clause,
                    candidate,
                    clause_type,
                    similarity_score=candidate.get("similarity_score", 0.0),
                )

                if contradiction:
                    contradictions.append(contradiction)

        self.metrics.update(
            {
                "clauses_processed": len(clauses),
                "vector_searches": vector_searches,
                "llm_calls": llm_calls,
            }
        )
        logger.info(
            "rag.contradiction_analysis",
            extra={
                "clauses_processed": len(clauses),
                "vector_searches": vector_searches,
                "llm_calls": llm_calls,
                "contradictions": len(contradictions),
            },
        )

        return contradictions
    
    def _detect_contradiction(
        self,
        clause_a: Dict,
        clause_b: Dict,
        clause_type: str,
        similarity_score: float = 0.0,
    ) -> Dict | None:
        """
        Detect if two clauses contradict each other
        Uses LLM for semantic analysis
        """
        
        base_prompt = f"""
Analyze if these two clauses from different contracts contradict or conflict. Restrict ALL reasoning to Indian law only. If applicability to Indian law is unclear, state that the clause may be unenforceable or ambiguous under Indian law. Do NOT reference US/UK/EU or international law.

Document A: {clause_a.get('document_name', 'Unknown')}
Section: {clause_a.get('section', 'N/A')}
{clause_a.get('text', '')}

Document B: {clause_b.get('document_name', 'Unknown')}
Section: {clause_b.get('section', 'N/A')}
{clause_b.get('text', '')}

Respond ONLY as JSON with:
{{
    "has_contradiction": true/false,
    "contradiction_type": "direct"|"partial"|"ambiguous",
    "risk_level": "high"|"medium"|"low",
    "summary": "One sentence summary",
    "explanation": "Plain English explanation for a non-lawyer",
    "indian_law_context": "How this applies in India or if unenforceable",
    "recommendations": ["action1", "action2"],
    "requires_lawyer": true/false
}}

Always include this disclaimer verbatim: "This analysis is for informational purposes only and does not constitute legal advice under Indian law."
If legal reasoning falls outside Indian jurisdiction, refuse and explain why.
"""

        strict_prompt = base_prompt + "\nReturn STRICT JSON only. No prose, no markdown."

        try:
            result = self._safe_llm_json(
                base_prompt,
                strict_prompt,
                required_keys={"has_contradiction", "contradiction_type", "risk_level"},
            )

            if not result or not result.get("has_contradiction"):
                return None

            allowed_types = {"direct", "partial", "ambiguous"}
            allowed_risks = {"high", "medium", "low"}

            contradiction_type = result.get("contradiction_type", "ambiguous")
            if contradiction_type not in allowed_types:
                contradiction_type = "ambiguous"

            risk_level = result.get("risk_level", "medium")
            if risk_level not in allowed_risks:
                risk_level = "medium"

            confidence = self._compute_confidence(
                similarity_score=similarity_score,
                contradiction_type=contradiction_type,
                risk_level=risk_level,
            )

            return {
                "title": f"Conflict in {clause_type}",
                "summary": result.get("summary", ""),
                "clauses": [
                    {**clause_a, "similarity_score": similarity_score},
                    {**clause_b, "similarity_score": similarity_score},
                ],
                "risk_level": risk_level,
                "risk_explanation": result.get("explanation", ""),
                "indian_law_note": result.get("indian_law_context"),
                "recommendations": result.get("recommendations", []),
                "requires_lawyer": result.get("requires_lawyer", risk_level == "high"),
                "confidence_score": confidence,
                "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law.",
            }
        except Exception:
            logger.exception("rag.contradiction_detection_failed")
            return None
    
    def answer_question(self, question: str) -> Dict:
        """
        Answer user questions about contracts using RAG
        
        Args:
            question: User question
            
        Returns:
            Answer with evidence
        """
        
        # Generate embedding for question
        question_embedding = self.embeddings.embed_text(question)

        # Find relevant clauses with similarity scores
        relevant_clauses = self.vector_db.search(question_embedding, top_k=6)

        # Build context
        context = "Relevant contract clauses (Indian law only):\n"
        for clause in relevant_clauses:
            context += f"\n{clause['document_name']} - Section {clause['section']}:\n"
            context += clause['text'][:500] + "...\n"

        prompt = f"""
Answer strictly under Indian law. If applicability is unclear, say the clause may be unenforceable or ambiguous under Indian law. Do NOT reference US/UK/EU law.

{context}

Question: {question}

Answer ONLY as JSON:
{{
    "answer": "Clear, simple explanation in plain English",
    "confidence": 0.0-1.0,
    "requires_lawyer": true/false,
    "requires_lawyer_reason": "Why a lawyer is or isn't needed"
}}

Always include this disclaimer verbatim: "This analysis is for informational purposes only and does not constitute legal advice under Indian law." If legal reasoning falls outside Indian jurisdiction, refuse and explain why.
"""

        strict_prompt = prompt + "\nReturn STRICT JSON only."

        try:
            result = self._safe_llm_json(
                prompt,
                strict_prompt,
                required_keys={"answer", "confidence", "requires_lawyer"},
            ) or {}

            avg_similarity = (
                sum(c.get("similarity_score", 0.0) for c in relevant_clauses) / len(relevant_clauses)
                if relevant_clauses
                else 0.0
            )

            confidence = float(result.get("confidence", 0.5))
            if avg_similarity < 0.45:
                confidence *= 0.6
                requires_lawyer = True
            else:
                requires_lawyer = bool(result.get("requires_lawyer", False))

            evidence = [
                {
                    "document": c.get("document_name"),
                    "section": c.get("section"),
                    "text": c.get("text", "")[:200],
                    "similarity_score": c.get("similarity_score", 0.0),
                }
                for c in relevant_clauses
            ]

            return {
                "question": question,
                "answer": result.get("answer", "Unable to answer"),
                "evidence": evidence,
                "confidence_score": round(confidence, 3),
                "requires_lawyer": requires_lawyer,
                "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law.",
                "similarity_average": round(avg_similarity, 3),
            }
        except Exception:
            logger.exception("rag.answer_question_failed")
            return {
                "question": question,
                "answer": "I couldn't process this question. Please try rephrasing.",
                "evidence": [],
                "confidence_score": 0.0,
                "requires_lawyer": True,
                "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law.",
            }

    def _get_clause_embedding(self, clause: Dict) -> List[float]:
        """Fetch embedding from vector DB or compute if missing."""

        try:
            if "embedding_index" in clause and self.vector_db.embeddings is not None:
                idx = clause["embedding_index"]
                return self.vector_db.embeddings[int(idx)].tolist()
        except Exception:
            logger.exception("rag.embedding_lookup_failed")

        return self.embeddings.embed_text(clause.get("text", ""))

    def _safe_llm_json(
        self,
        prompt: str,
        strict_prompt: str,
        required_keys: set,
    ) -> Optional[Dict]:
        """Call LLM and parse JSON with a retry for stricter prompt."""

        def _parse(response_text: str) -> Optional[Dict]:
            try:
                parsed = json.loads(response_text)
                if not required_keys.issubset(parsed.keys()):
                    return None
                return parsed
            except JSONDecodeError:
                return None

        # First attempt
        response = self.llm.generate(prompt)
        parsed = _parse(response)
        if parsed:
            return parsed

        # Retry with strict JSON-only prompt
        response_strict = self.llm.generate(strict_prompt, temperature=0.1)
        parsed = _parse(response_strict)
        return parsed

    def _compute_confidence(
        self,
        similarity_score: float,
        contradiction_type: str,
        risk_level: str,
    ) -> float:
        """Compute confidence based on similarity, contradiction type, and risk."""

        confidence = similarity_score if similarity_score > 0 else 0.4

        type_boost = {
            "direct": 0.2,
            "partial": 0.1,
            "ambiguous": -0.1,
        }.get(contradiction_type, -0.05)

        risk_boost = {
            "high": 0.2,
            "medium": 0.1,
            "low": -0.1,
        }.get(risk_level, 0)

        confidence = confidence + type_boost + risk_boost
        confidence = max(0.0, min(1.0, confidence))
        return round(confidence, 3)
