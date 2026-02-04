"""
PactLens Backend - RAG (Retrieval Augmented Generation) Pipeline
Handles embeddings, similarity search, and AI-powered analysis

Per-analysis operation:
- FAISS/Vector DB created fresh for each analysis
- No global state or persistence
- Automatic memory cleanup after analysis completes
"""

import logging
import re
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from json import JSONDecodeError

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Main RAG pipeline for contract analysis.

    Operates on a per-analysis basis with:
    - Session-specific vector database
    - No global state
    - Automatic resource cleanup
    """

    def __init__(self, embeddings_service, llm_service):
        self.embeddings = embeddings_service
        self.llm = llm_service
        self.metrics = {
            "clauses_processed": 0,
            "vector_searches": 0,
            "llm_calls": 0,
        }

    def analyze_contradictions(self, clauses: List[Dict], vector_db) -> List[Dict]:
        """
        Optimized contradiction detection with minimal LLM calls.
        
        Optimizations:
        - O(n log n) complexity via pre-grouping by clause type
        - Top-K similarity search (only 3-5 comparisons per clause)
        - Same-document filtering
        - Duplicate pair prevention
        - Similarity threshold filtering (>0.6 only)
        
        Args:
            clauses: List of extracted clauses
            vector_db: Session-specific vector database
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        processed_pairs = set()  # Prevent A↔B and B↔A duplication
        vector_searches = 0
        llm_calls = 0
        batch_pairs = []
        batch_size = 5  # Batch 5–10 clause pairs per LLM call
        
        # 🚀 OPTIMIZATION 1: Pre-group clauses by type and document
        # Reduces search space from O(n²) to O(n log n)
        clauses_by_type = {}
        unique_docs = set()
        
        for clause in clauses:
            clause_type = clause.get("clause_type", "General")
            doc_id = clause.get("document_id")
            unique_docs.add(doc_id)
            
            if clause_type not in clauses_by_type:
                clauses_by_type[clause_type] = []
            clauses_by_type[clause_type].append(clause)
        
        print(f"\n🔍 ANALYZING {len(clauses)} clauses from {len(unique_docs)} documents")
        print(f"Grouped by type: {[(t, len(c)) for t, c in clauses_by_type.items()]}")
        
        # 🚀 OPTIMIZATION 2: Only process types with clauses from multiple documents
        for clause_type, type_clauses in clauses_by_type.items():
            # Skip if all clauses are from same document (no cross-doc comparison possible)
            docs_in_type = set(c.get("document_id") for c in type_clauses)
            if len(docs_in_type) < 2:
                print(f"⏭️  Skipping '{clause_type}' - only in 1 document")
                continue
            
            print(f"\n📋 Processing '{clause_type}' ({len(type_clauses)} clauses from {len(docs_in_type)} docs)")
            
            for clause in type_clauses:
                clause_doc = clause.get("document_id")
                
                # Get embedding for this clause
                query_embedding = self._get_clause_embedding(clause)
                
                # 🚀 OPTIMIZATION 3: Top-K similarity search with threshold
                # Only get top 3 most similar clauses (not all)
                similar_clauses = vector_db.query(
                    query_embedding,
                    clause_type=clause_type,  # Same type only
                    exclude_document_id=clause_doc,  # Different document only
                    top_k=3,  # Reduced from 5 to 3 for speed
                )
                
                vector_searches += 1
                
                # 🚀 HYBRID APPROACH: Embeddings + Regex + Numeric
                # Accept clauses with EITHER:
                # 1. High embedding similarity (>0.60)
                # 2. Matching regex patterns (same clause type indicators)
                # 3. Conflicting numbers/dates (potential contradictions)
                
                hybrid_matches = []
                for c in similar_clauses:
                    embedding_sim = c.get("similarity_score", 0)
                    clause_text = clause.get("text", "")
                    candidate_text = c.get("text", "")
                    
                    # Signal 1: Embedding similarity
                    has_embedding_match = embedding_sim > 0.60
                    
                    # Signal 2: Regex pattern match (same clause patterns)
                    has_regex_match = self._has_pattern_overlap(clause_text, candidate_text)
                    
                    # Signal 3: Numeric/date conflicts (different values)
                    has_numeric_conflict = self._has_numeric_conflict(clause_text, candidate_text)
                    
                    # Accept if ANY signal is positive
                    if has_embedding_match or has_regex_match or has_numeric_conflict:
                        # Store match reason for debugging
                        c["match_reason"] = []
                        if has_embedding_match:
                            c["match_reason"].append(f"embedding:{embedding_sim:.2f}")
                        if has_regex_match:
                            c["match_reason"].append("regex")
                        if has_numeric_conflict:
                            c["match_reason"].append("numeric")
                        hybrid_matches.append(c)
                
                if not hybrid_matches:
                    continue
                
                print(f"  ✅ Found {len(hybrid_matches)} hybrid matches for clause from {clause_doc[:8]}")
                
                for candidate in hybrid_matches:
                    print(f"     → Match reason: {', '.join(candidate.get('match_reason', []))}")
                    # 🚀 OPTIMIZATION 5: Prevent duplicate pairs
                    pair_key = tuple(sorted([clause.get("id"), candidate.get("id")]))
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)

                    # 🚀 NEW OPTIMIZATION: If extremely similar, avoid LLM unless rules detect conflict
                    similarity_score = candidate.get("similarity_score", 0.0)
                    if similarity_score >= 0.92:
                        # Rule-based quick check (numbers/dates) to detect potential conflicts
                        potential_conflict = self._rule_based_conflict(
                            clause.get("text", ""),
                            candidate.get("text", ""),
                        )

                        if not potential_conflict:
                            # Clauses are highly similar and no rule-based conflict detected
                            # Skip LLM call to save cost and latency
                            continue
                    
                    batch_pairs.append(
                        {
                            "pair_id": len(batch_pairs) + 1,
                            "clause_a": clause,
                            "clause_b": candidate,
                            "clause_type": clause_type,
                            "similarity_score": similarity_score,
                        }
                    )

                    if len(batch_pairs) >= batch_size:
                        llm_calls += 1
                        print(f"  🤖 LLM batch call #{llm_calls}: {len(batch_pairs)} pairs")
                        batch_results = self._detect_contradictions_batch(batch_pairs)
                        contradictions.extend(batch_results)
                        batch_pairs = []

        # Process any remaining pairs in the final batch
        if batch_pairs:
            llm_calls += 1
            print(f"  🤖 LLM batch call #{llm_calls}: {len(batch_pairs)} pairs")
            batch_results = self._detect_contradictions_batch(batch_pairs)
            contradictions.extend(batch_results)

        self.metrics.update({
            "clauses_processed": len(clauses),
            "vector_searches": vector_searches,
            "llm_calls": llm_calls,
        })
        
        print(f"\n{'='*60}")
        print(f"📊 ANALYSIS COMPLETE")
        print(f"   Clauses: {len(clauses)} | Searches: {vector_searches} | LLM calls: {llm_calls}")
        print(f"   Contradictions found: {len(contradictions)}")
        print(f"{'='*60}\n")
        
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

    def _detect_contradictions_batch(self, pairs: List[Dict]) -> List[Dict]:
        """
        Batch multiple clause pair comparisons into a single LLM call.

        Args:
            pairs: List of dicts with keys: pair_id, clause_a, clause_b, clause_type, similarity_score

        Returns:
            List of detected contradictions (same format as _detect_contradiction)
        """
        if not pairs:
            return []

        prompt = self._build_batch_prompt(pairs)
        strict_prompt = prompt + "\nReturn STRICT JSON only. No prose, no markdown."

        try:
            results = self._safe_llm_json_list(
                prompt,
                strict_prompt,
                required_keys={"pair_id", "has_contradiction"},
            )

            if not results:
                # Fallback: process individually on parse failure
                logger.warning("rag.batch_parse_failed_fallback_to_single")
                return self._fallback_single_pairs(pairs)

            results_by_id = {r.get("pair_id"): r for r in results if isinstance(r, dict)}

            contradictions = []
            for pair in pairs:
                pair_id = pair.get("pair_id")
                result = results_by_id.get(pair_id)

                if not result:
                    # Partial failure: fallback to single pair
                    single = self._detect_contradiction(
                        pair["clause_a"],
                        pair["clause_b"],
                        pair["clause_type"],
                        similarity_score=pair.get("similarity_score", 0.0),
                    )
                    if single:
                        contradictions.append(single)
                    continue

                if not result.get("has_contradiction"):
                    continue

                allowed_types = {"direct", "partial", "ambiguous"}
                allowed_risks = {"high", "medium", "low"}

                contradiction_type = result.get("contradiction_type", "ambiguous")
                if contradiction_type not in allowed_types:
                    contradiction_type = "ambiguous"

                risk_level = result.get("risk_level", "medium")
                if risk_level not in allowed_risks:
                    risk_level = "medium"

                confidence = self._compute_confidence(
                    similarity_score=pair.get("similarity_score", 0.0),
                    contradiction_type=contradiction_type,
                    risk_level=risk_level,
                )

                contradictions.append(
                    {
                        "title": f"Conflict in {pair.get('clause_type')}",
                        "summary": result.get("summary", ""),
                        "clauses": [
                            {**pair["clause_a"], "similarity_score": pair.get("similarity_score", 0.0)},
                            {**pair["clause_b"], "similarity_score": pair.get("similarity_score", 0.0)},
                        ],
                        "risk_level": risk_level,
                        "risk_explanation": result.get("explanation", ""),
                        "indian_law_note": result.get("indian_law_context"),
                        "recommendations": result.get("recommendations", []),
                        "requires_lawyer": result.get("requires_lawyer", risk_level == "high"),
                        "confidence_score": confidence,
                        "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law.",
                    }
                )

            return contradictions
        except Exception:
            logger.exception("rag.batch_contradiction_detection_failed")
            return self._fallback_single_pairs(pairs)

    def _build_batch_prompt(self, pairs: List[Dict]) -> str:
        """
        Build a batch prompt with numbered clause pairs and clear JSON output requirements.
        """
        header = (
            "Analyze each clause pair below for contradictions under Indian law only. "
            "If applicability to Indian law is unclear, state that the clause may be unenforceable or ambiguous. "
            "Do NOT reference US/UK/EU or international law.\n\n"
            "Return ONLY a JSON array with one item per pair, preserving pair_id.\n"
            "Output format:\n"
            "[\n"
            "  {\"pair_id\": 1, \"has_contradiction\": true/false, \"contradiction_type\": \"direct|partial|ambiguous\", "
            "\"risk_level\": \"high|medium|low\", \"summary\": \"...\", \"explanation\": \"...\", "
            "\"indian_law_context\": \"...\", \"recommendations\": [\"...\"], \"requires_lawyer\": true/false},\n"
            "  ...\n"
            "]\n\n"
        )

        body_lines = []
        for pair in pairs:
            clause_a = pair["clause_a"]
            clause_b = pair["clause_b"]
            pair_id = pair["pair_id"]
            clause_type = pair.get("clause_type", "General")

            body_lines.append(
                f"PAIR {pair_id} (Type: {clause_type}):\n"
                f"Document A: {clause_a.get('document_name', 'Unknown')} | Section: {clause_a.get('section', 'N/A')}\n"
                f"{clause_a.get('text', '')}\n\n"
                f"Document B: {clause_b.get('document_name', 'Unknown')} | Section: {clause_b.get('section', 'N/A')}\n"
                f"{clause_b.get('text', '')}\n"
            )

        return header + "\n---\n".join(body_lines)

    def _safe_llm_json_list(
        self,
        prompt: str,
        strict_prompt: str,
        required_keys: set,
    ) -> Optional[List[Dict]]:
        """
        Call LLM and parse JSON array response safely.
        """

        def _parse(txt: str) -> Optional[List[Dict]]:
            try:
                data = json.loads(txt)
                if not isinstance(data, list):
                    return None
                for item in data:
                    if not isinstance(item, dict) or not required_keys.issubset(item.keys()):
                        return None
                return data
            except JSONDecodeError:
                return None

        r = self.llm.generate(prompt)
        parsed = _parse(r)
        if parsed:
            return parsed

        r = self.llm.generate(strict_prompt, temperature=0.1)
        return _parse(r)

    def _fallback_single_pairs(self, pairs: List[Dict]) -> List[Dict]:
        """
        Safe fallback: run single-pair detection when batch parsing fails.
        """
        contradictions = []
        for pair in pairs:
            single = self._detect_contradiction(
                pair["clause_a"],
                pair["clause_b"],
                pair["clause_type"],
                similarity_score=pair.get("similarity_score", 0.0),
            )
            if single:
                contradictions.append(single)
        return contradictions

    def answer_question(self, question: str, vector_db) -> Dict:

        question_embedding = self.embeddings.embed_text(question)

        relevant_clauses = vector_db.search(question_embedding, top_k=6)

        context = ""
        for clause in relevant_clauses:
            context += clause.get("text", "")[:500] + "\n"

        prompt = f"""
Answer under Indian law only.

{context}

Question: {question}

Return JSON:
{{
    "answer": "",
    "confidence": 0.0,
    "requires_lawyer": false
}}
"""

        strict_prompt = prompt + "\nReturn STRICT JSON only."

        try:
            result = self._safe_llm_json(
                prompt,
                strict_prompt,
                required_keys={"answer", "confidence", "requires_lawyer"},
            ) or {}

            return {
                "question": question,
                "answer": result.get("answer", ""),
                "confidence_score": result.get("confidence", 0.5),
                "requires_lawyer": result.get("requires_lawyer", False),
            }

        except Exception:
            logger.exception("rag.answer_question_failed")
            return {
                "question": question,
                "answer": "Failed to answer",
                "confidence_score": 0.0,
                "requires_lawyer": True,
            }

    # ✅ FIXED HERE
    def _get_clause_embedding(self, clause: Dict) -> List[float]:
        """Always compute embedding from text (no global vector_db)."""
        return self.embeddings.embed_text(clause.get("text", ""))

    def _safe_llm_json(
        self,
        prompt: str,
        strict_prompt: str,
        required_keys: set,
    ) -> Optional[Dict]:

        def _parse(txt):
            try:
                data = json.loads(txt)
                if required_keys.issubset(data.keys()):
                    return data
            except JSONDecodeError:
                return None
            return None

        r = self.llm.generate(prompt)
        parsed = _parse(r)
        if parsed:
            return parsed

        r = self.llm.generate(strict_prompt, temperature=0.1)
        return _parse(r)

    def _rule_based_conflict(self, text_a: str, text_b: str) -> bool:
        """
        Lightweight rule-based conflict check for very similar clauses.

        Rules:
        - Duration numbers differ (e.g., 30 days vs 60 days)
        - Payment amounts differ (e.g., 10,000 vs 15,000)
        - Dates differ (e.g., 01/01/2025 vs 01/03/2025)

        Returns:
            True if potential conflict found, else False.
        """
        numbers_a = self._extract_numbers(text_a)
        numbers_b = self._extract_numbers(text_b)

        dates_a = self._extract_dates(text_a)
        dates_b = self._extract_dates(text_b)

        # If both have numbers but sets differ, flag potential conflict
        if numbers_a and numbers_b and numbers_a != numbers_b:
            return True

        # If both have dates but sets differ, flag potential conflict
        if dates_a and dates_b and dates_a != dates_b:
            return True

        return False

    def _extract_numbers(self, text: str) -> set:
        """
        Extract numeric values (including currency-like numbers) from text.
        Examples: 30, 60, 10,000, 15.5
        """
        # Match integers and decimals with optional commas
        pattern = r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b"
        matches = re.findall(pattern, text)

        # Normalize: remove commas for comparison
        normalized = {m.replace(",", "") for m in matches}
        return normalized

    def _extract_dates(self, text: str) -> set:
        """
        Extract common date formats from text.
        Examples: 01/01/2025, 2025-01-31, 1 Jan 2025
        """
        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # 01/01/2025 or 1-1-25
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",      # 2025-01-31
            r"\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s\d{2,4}\b",
        ]

        matches = set()
        for pattern in date_patterns:
            found = re.findall(pattern, text, flags=re.IGNORECASE)
            matches.update([f.lower() for f in found])

        return matches
    
    def _has_pattern_overlap(self, text_a: str, text_b: str) -> bool:
        """
        Check if two clauses share common legal patterns/keywords.
        Returns True if they likely discuss the same topic.
        """
        # Define pattern groups for common contract elements
        pattern_groups = [
            # Confidentiality patterns
            [r"confidential", r"disclosure", r"non-disclosure", r"proprietary", r"secret"],
            # Termination patterns
            [r"terminat", r"end\s+agreement", r"cancel", r"rescind", r"notice\s+period"],
            # Payment patterns
            [r"payment", r"compensation", r"fee", r"invoice", r"remuneration"],
            # Liability patterns
            [r"liability", r"indemnif", r"warrant", r"represent", r"guarantee"],
            # Duration patterns
            [r"\d+\s+days?", r"\d+\s+months?", r"\d+\s+years?", r"duration", r"term"],
            # Non-compete patterns
            [r"non-compete", r"non\s+compete", r"restrict", r"prohibit", r"not\s+engage"],
        ]
        
        text_a_lower = text_a.lower()
        text_b_lower = text_b.lower()
        
        # Check each pattern group
        for patterns in pattern_groups:
            matches_a = sum(1 for p in patterns if re.search(p, text_a_lower))
            matches_b = sum(1 for p in patterns if re.search(p, text_b_lower))
            
            # If both clauses have 2+ matches from same pattern group, they overlap
            if matches_a >= 2 and matches_b >= 2:
                return True
        
        return False
    
    def _has_numeric_conflict(self, text_a: str, text_b: str) -> bool:
        """
        Detect if two clauses have conflicting numeric values.
        Returns True if they discuss same topic but have different numbers.
        """
        numbers_a = self._extract_numbers(text_a)
        numbers_b = self._extract_numbers(text_b)
        dates_a = self._extract_dates(text_a)
        dates_b = self._extract_dates(text_b)
        
        # Must have numbers/dates in BOTH clauses
        if not (numbers_a or dates_a) or not (numbers_b or dates_b):
            return False
        
        # Check for conflicting numbers
        if numbers_a and numbers_b:
            # If they share NO common numbers, likely conflict
            common_numbers = numbers_a & numbers_b
            if len(common_numbers) == 0 and len(numbers_a) > 0 and len(numbers_b) > 0:
                return True
        
        # Check for conflicting dates
        if dates_a and dates_b:
            common_dates = dates_a & dates_b
            if len(common_dates) == 0:
                return True
        
        return False

    def _compute_confidence(
        self,
        similarity_score: float,
        contradiction_type: str,
        risk_level: str,
    ) -> float:

        confidence = similarity_score if similarity_score else 0.4

        type_boost = {"direct": 0.2, "partial": 0.1, "ambiguous": -0.1}.get(
            contradiction_type, 0
        )

        risk_boost = {"high": 0.2, "medium": 0.1, "low": -0.1}.get(risk_level, 0)

        confidence += type_boost + risk_boost
        return round(max(0.0, min(1.0, confidence)), 3)
