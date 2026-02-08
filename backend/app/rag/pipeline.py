import logging
import re
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RAGPipeline:

    def __init__(self, embeddings_service, llm_service):
        self.embeddings = embeddings_service
        self.llm = llm_service

    # =========================================================
    # MAIN ENTRY
    # =========================================================

    def analyze_contradictions(
        self,
        clauses: List[Dict],
        vector_db,
        batch_size: int = 5,
        similarity_threshold: float = 0.65,
        confidence_threshold: float = 0.55,
    ) -> List[Dict]:

        logger.info(f"Analyzing {len(clauses)} clauses")

        contradictions = []
        processed_pairs = set()
        batch_pairs = []

        clauses_by_type = self._group_by_type(clauses)

        for clause_type, type_clauses in clauses_by_type.items():

            docs = {c.get("document_id") for c in type_clauses}
            if len(docs) < 2:
                continue

            for clause in type_clauses:

                query_emb = self._get_clause_embedding(clause)

                candidates = vector_db.query(
                    query_emb,
                    clause_type=clause_type,
                    exclude_document_id=clause.get("document_id"),
                    top_k=5,
                )

                for cand in candidates:

                    sim = cand.get("similarity_score", 0)

                    if not self._is_valid_match(
                        clause, cand, sim, similarity_threshold
                    ):
                        continue

                    pair_key = tuple(sorted([
                        clause.get("id"),
                        cand.get("id"),
                    ]))

                    if pair_key in processed_pairs:
                        continue

                    processed_pairs.add(pair_key)
                    
                    # 🔥 DEBUG
                    print("MATCH FOUND:", clause["text"][:60])

                    batch_pairs.append({
                        "pair_id": len(batch_pairs)+1,
                        "clause_a": clause,
                        "clause_b": cand,
                        "clause_type": clause_type,
                        "similarity_score": sim,
                    })

                    if len(batch_pairs) >= batch_size:
                        contradictions.extend(
                            self._process_batch(batch_pairs)
                        )
                        batch_pairs = []

        if batch_pairs:
            contradictions.extend(
                self._process_batch(batch_pairs)
            )

        print(f"\n📊 Before filtering: {len(contradictions)} contradictions")
        
        # 🔥 DEBUG: Check first contradiction structure
        if contradictions:
            print(f"🔍 Sample contradiction structure:")
            print(f"  - Title: {contradictions[0].get('title', 'N/A')}")
            print(f"  - Clauses count: {len(contradictions[0].get('clauses', []))}")
            if contradictions[0].get('clauses'):
                print(f"  - Clause A keys: {list(contradictions[0]['clauses'][0].keys())}")
                print(f"  - Clause A text length: {len(contradictions[0]['clauses'][0].get('text', ''))}")
        
        # 🔥 Confidence filtering
        contradictions = [
            c for c in contradictions
            if c.get("confidence_score", 0) >= confidence_threshold
        ]
        
        print(f"📊 After confidence filter (>={confidence_threshold}): {len(contradictions)} contradictions")

        # 🔥 Smart deduplication
        contradictions = self._smart_dedupe(contradictions)
        print(f"📊 After deduplication: {len(contradictions)} contradictions")
        
        # 🔥 Group similar contradictions by clause type
        contradictions = self._collapse_by_type(contradictions)
        print(f"📊 After collapsing by type: {len(contradictions)} contradiction groups")

        # 🔥 Sort by: 1) Risk level, 2) Priority (legal importance), 3) Confidence
        contradictions.sort(
            key=lambda x: (
                -{"high":3,"medium":2,"low":1}[x.get("risk_level","low")],  # High risk first
                x.get("priority", 99),  # Legal priority order
                -x.get("confidence_score",0)  # High confidence first
            )
        )
        print(f"📊 Sorted by risk, priority, and confidence")

        logger.info(f"Final contradictions: {len(contradictions)}")
        print(f"\n🎉 FINAL CONTRADICTIONS COUNT: {len(contradictions)}")
        print(f"FINAL CONTRADICTIONS: {contradictions}\n")

        return contradictions

    # =========================================================
    # MATCHING LOGIC
    # =========================================================

    def _is_valid_match(self, clause, candidate, similarity, threshold):

        text_a = clause.get("text","")
        text_b = candidate.get("text","")

        has_regex = self._has_pattern_overlap(text_a, text_b)
        has_numeric = self._has_numeric_conflict(text_a, text_b)

        # 🔥 STRICTER RULES - require BOTH similarity AND semantic conflict
        if has_numeric and similarity >= 0.60:
            return True
        
        if has_regex and similarity >= 0.70:
            return True
        
        if similarity >= 0.75:
            return True

        return False

    # =========================================================
    # BATCH PROCESSING
    # =========================================================

    def _process_batch(self, pairs):

        results = self._detect_contradictions_batch(pairs)
        return results or []

    # =========================================================
    # DEDUPLICATION
    # =========================================================

    def _smart_dedupe(self, contradictions):
        """Remove true duplicates based on clause text pairs (text-based hashing)"""
        seen = set()
        unique = []

        print(f"\n🔍 DEDUPE DEBUG: Starting with {len(contradictions)} contradictions")

        for idx, c in enumerate(contradictions):
            try:
                a = c["clauses"][0]["text"].strip().lower()[:100]  # First 100 chars
                b = c["clauses"][1]["text"].strip().lower()[:100]
                key = tuple(sorted([a, b]))

                if idx < 3:  # Show first 3
                    print(f"  Pair {idx+1}: '{a[:50]}...' vs '{b[:50]}...'")
                
                if key not in seen:
                    seen.add(key)
                    unique.append(c)
                else:
                    if idx < 3:
                        print(f"    ❌ DUPLICATE - already seen")
            except Exception as e:
                print(f"  ⚠️ Error processing contradiction {idx}: {e}")
                # Add it anyway if there's an error
                unique.append(c)
        
        # 🔥 Fix #3: Debug print
        print(f"🧹 After dedupe: {len(unique)} unique contradictions (removed {len(contradictions) - len(unique)} duplicates)\n")

        return unique

    def _generate_smart_summary(self, clause_type, clauses, conflict_count):
        """Generate human-readable summary based on clause type and content"""
        
        if clause_type == "Confidentiality":
            # Extract duration info from clause text
            durations = []
            for clause in clauses:
                text = clause.get("text", "").lower()
                if "year" in text:
                    import re
                    nums = re.findall(r'(\d+)\s*year', text)
                    durations.extend([int(n) for n in nums])
            
            if durations:
                min_dur = min(durations)
                max_dur = max(durations)
                if min_dur == max_dur:
                    return f"Confidentiality terms specify {min_dur} year duration with varying conditions. Review for consistency."
                else:
                    return f"Confidentiality terms vary between {min_dur}–{max_dur} years and include penalty clauses. Standardization recommended."
            return f"Confidentiality clauses contain conflicting terms. Review {conflict_count} instances for consistency."
        
        elif clause_type == "Compensation":
            # Extract salary info
            amounts = []
            for clause in clauses:
                text = clause.get("text", "")
                import re
                # Look for INR amounts
                nums = re.findall(r'INR\s*([\d,]+)', text)
                amounts.extend(nums)
            
            if amounts:
                return f"Payment terms differ across documents (INR {', '.join(amounts[:3])}). Define which prevails."
            return f"Compensation terms are inconsistent across {conflict_count} clauses. Ensure clarity to avoid disputes."
        
        elif clause_type == "Notice Period":
            # Extract notice periods
            periods = []
            for clause in clauses:
                text = clause.get("text", "").lower()
                import re
                nums = re.findall(r'(\d+)\s*day', text)
                periods.extend([int(n) for n in nums])
            
            if periods:
                return f"Notice period requirements vary between {min(periods)}–{max(periods)} days. Standardize to avoid confusion."
            return f"Notice period clauses are inconsistent. Review {conflict_count} instances."
        
        else:
            # Generic summary for other types
            return f"{conflict_count} inconsistent clauses detected. These may affect enforceability under Indian law."

    def _is_valid_clause(self, clause_text):
        """Filter out title/header clauses that aren't real content"""
        if not clause_text:
            return False
        
        text = clause_text.strip()
        
        # Skip very short text (likely headers)
        if len(text.split()) < 8:
            return False
        
        # Skip all-caps headers
        if text.isupper():
            return False
        
        # Skip document titles
        if any(keyword in text.upper() for keyword in ["EMPLOYMENT AGREEMENT", "OFFER LETTER", "COMPANY:", "LOCATION:"]):
            return False
        
        return True
    
    def _collapse_by_type(self, contradictions):
        """Collapse multiple contradictions of the same type into grouped summaries"""
        
        # Friendly names and legal impact descriptions
        FRIENDLY_NAMES = {
            "General": "Contract Terms",
            "Confidentiality": "Confidentiality",
            "Compensation": "Compensation",
            "Termination": "Termination",
            "Notice": "Notice Period",
            "Jurisdiction": "Jurisdiction"
        }
        
        IMPACT_MESSAGES = {
            "Confidentiality": "Conflicting confidentiality durations may weaken enforceability and create ambiguity post-employment under Indian Contract Act, 1872.",
            "Compensation": "Payment term differences can lead to disputes and may be challenged under principles of contract clarity.",
            "Termination": "Inconsistent termination clauses may reduce enforceability and create legal uncertainty.",
            "Contract Terms": "Inconsistent obligations or timelines may reduce legal clarity and enforceability.",
            "Notice Period": "Varying notice requirements across documents create ambiguity and potential disputes.",
            "Jurisdiction": "Conflicting jurisdiction clauses may complicate dispute resolution."
        }
        
        # Context-specific recommendations
        RECOMMENDATIONS = {
            "Confidentiality": [
                "Standardize confidentiality duration across all documents",
                "Consider non-compete clause limitations under Indian law (typically 2-3 years maximum)",
                "Consult a qualified lawyer practicing in India"
            ],
            "Compensation": [
                "Ensure salary and payment terms are consistent across all documents",
                "Define which document takes precedence in case of mismatch",
                "Consult a qualified lawyer practicing in India"
            ],
            "Termination": [
                "Harmonize termination conditions across all agreements",
                "Clarify notice periods and termination rights",
                "Consult a qualified lawyer practicing in India"
            ],
            "Notice Period": [
                "Standardize notice period requirements",
                "Ensure consistency between employment agreement and offer letter",
                "Consult a qualified lawyer practicing in India"
            ],
            "Contract Terms": [
                "Review all conflicting terms for consistency",
                "Harmonize obligations across all documents",
                "Consult a qualified lawyer practicing in India"
            ]
        }
        
        # Priority order for legal importance
        PRIORITY_ORDER = {
            "Confidentiality": 1,
            "Compensation": 2,
            "Termination": 3,
            "Notice": 4,
            "Jurisdiction": 5,
            "Contract Terms": 6
        }
        
        # Group by clause type
        by_type = {}
        for c in contradictions:
            clause_type = c["clauses"][0].get("clause_type", "General")
            if clause_type not in by_type:
                by_type[clause_type] = []
            by_type[clause_type].append(c)
        
        collapsed = []
        
        for clause_type, items in by_type.items():
            display_type = FRIENDLY_NAMES.get(clause_type, clause_type)
            impact = IMPACT_MESSAGES.get(display_type, f"These inconsistencies may weaken enforceability under Indian law.")
            
            if len(items) == 1:
                # Only one contradiction - enhance with better messaging
                item = items[0].copy()
                item["title"] = f"{display_type} Conflict"
                item["risk_explanation"] = impact
                item["clause_type_display"] = display_type
                item["priority"] = PRIORITY_ORDER.get(display_type, 99)
                collapsed.append(item)
            else:
                # Multiple contradictions - create grouped summary
                all_clause_pairs = []
                risk_levels = [c.get("risk_level", "low") for c in items]
                
                # Collect all clause pairs
                for c in items:
                    all_clause_pairs.extend(c.get("clauses", []))
                
                # 🔥 Filter out title/header clauses and deduplicate by text
                unique_clauses = {}
                for clause in all_clause_pairs:
                    text = clause.get("text", "").strip()
                    if self._is_valid_clause(text):
                        key = text.lower()
                        if key not in unique_clauses:
                            unique_clauses[key] = clause
                
                deduped_clauses = list(unique_clauses.values())[:10]  # Limit to 10 unique clauses
                
                # Determine highest risk
                if "high" in risk_levels:
                    risk = "high"
                elif "medium" in risk_levels:
                    risk = "medium"
                else:
                    risk = "low"
                
                # Generate human-readable summary based on clause type
                summary = self._generate_smart_summary(display_type, deduped_clauses, len(items))
                
                # Get context-specific recommendations
                recommendations = RECOMMENDATIONS.get(display_type, [
                    f"Review all {len(items)} {display_type.lower()} conflicts for consistency",
                    "Harmonize terms across all documents to avoid disputes",
                    "Consult a qualified lawyer practicing in India"
                ])
                
                # Create grouped contradiction
                grouped = {
                    "title": f"Multiple {display_type} Conflicts",
                    "summary": summary,
                    "risk_level": risk,
                    "risk_explanation": impact,
                    "recommendations": recommendations,
                    "confidence_score": max(c.get("confidence_score", 0) for c in items),
                    "clauses": deduped_clauses,  # Use deduplicated clauses
                    "conflict_count": len(items),
                    "clause_type_display": display_type,
                    "priority": PRIORITY_ORDER.get(display_type, 99)
                }
                
                collapsed.append(grouped)
                print(f"  📦 Collapsed {len(items)} {clause_type} conflicts into '{display_type}' group ({len(deduped_clauses)} unique clauses)")
        
        return collapsed

    def _group_by_type(self, contradictions):
        """Group contradictions by clause type for organized display"""
        grouped = {}

        for c in contradictions:
            t = c["clauses"][0].get("clause_type", "General")

            if t not in grouped:
                grouped[t] = []

            grouped[t].append(c)

        return grouped

    # =========================================================
    # GROUPING
    # =========================================================

    def _group_by_type(self, clauses):
        groups = {}
        for c in clauses:
            t = c.get("clause_type","General")
            groups.setdefault(t, []).append(c)
        return groups

    # =========================================================
    # LLM BATCH DETECTION
    # =========================================================

    def _detect_contradictions_batch(self, pairs):

        if not pairs:
            return []

        prompt = self._build_batch_prompt(pairs)

        raw = self.llm.generate_answer(prompt, mode="contradiction", temperature=0.2)

        print("🤖 LLM RAW:", raw[:500])

        try:
            data = json.loads(raw)
        except Exception as e:
            logger.warning(f"Batch JSON parse failed: {e}")
            print(f"❌ JSON parse failed: {e}")
            return []

        contradictions = []

        # CASE 1: LLM returned single object
        if isinstance(data, dict):

            if not data.get("has_contradiction"):
                print("⚠️  LLM returned no contradiction (single object)")
                return []

            print(f"📦 LLM returned single object - applying to all {len(pairs)} pairs")

            for pair in pairs:
                # 🔥 Clone the result for each pair
                new_result = {
                    "title": f"Conflict in {pair['clause_type']}",
                    "summary": data.get("summary",""),
                    "risk_level": data.get("risk_level","medium"),
                    "risk_explanation": data.get("explanation",""),
                    "recommendations": data.get("recommendations",[]),
                    "confidence_score": 0.8
                }
                
                # Set unique clauses for this pair
                new_result["clauses"] = [
                    pair["clause_a"],
                    pair["clause_b"]
                ]
                
                contradictions.append(new_result)

            print(f"✅ Created {len(contradictions)} contradictions from single object")
            return contradictions

        # CASE 2: LLM returned list with pair_ids
        elif isinstance(data, list):

            print(f"📦 LLM returned list with {len(data)} items")
            results_by_id = {r["pair_id"]: r for r in data if "pair_id" in r}

            for pair in pairs:
                r = results_by_id.get(pair["pair_id"])
                if not r or not r.get("has_contradiction"):
                    continue

                # 🔥 Clone the result for each pair
                new_result = {
                    "title": f"Conflict in {pair['clause_type']}",
                    "summary": r.get("summary",""),
                    "risk_level": r.get("risk_level","medium"),
                    "risk_explanation": r.get("explanation",""),
                    "recommendations": r.get("recommendations",[]),
                    "confidence_score": 0.8
                }
                
                # Set unique clauses for this pair
                new_result["clauses"] = [
                    pair["clause_a"],
                    pair["clause_b"]
                ]
                
                contradictions.append(new_result)

            print(f"✅ Created {len(contradictions)} contradictions from list")
            return contradictions

        print("⚠️  Unknown data format from LLM")
        return []

    # =========================================================
    # PROMPT BUILDER
    # =========================================================

    def _build_batch_prompt(self, pairs):

        header = (
            "Analyze contradictions under Indian law.\n"
            "Return ONLY JSON array.\n\n"
        )

        blocks = []

        for p in pairs:
            a = p["clause_a"]
            b = p["clause_b"]

            blocks.append(
f"""
PAIR {p['pair_id']}:
A: {a.get("text","")}
B: {b.get("text","")}
"""
            )

        return header + "\n".join(blocks)

    # =========================================================
    # EMBEDDINGS
    # =========================================================

    def _get_clause_embedding(self, clause):
        return self.embeddings.embed_text(
            clause.get("text","")
        )

    # =========================================================
    # CONFIDENCE
    # =========================================================

    def _compute_confidence(
        self,
        similarity,
        ctype,
        risk,
    ):

        score = similarity

        if ctype == "direct":
            score += 0.2
        elif ctype == "partial":
            score += 0.1

        if risk == "high":
            score += 0.2
        elif risk == "low":
            score -= 0.1

        return round(max(0,min(1,score)),3)

    # =========================================================
    # PATTERN MATCHING
    # =========================================================

    def _has_pattern_overlap(self, a,b):
        words = ["terminate","payment","confidential","liability"]
        a=a.lower(); b=b.lower()
        return any(w in a and w in b for w in words)

    def _has_numeric_conflict(self,a,b):
        numsA=set(re.findall(r'\d+',a))
        numsB=set(re.findall(r'\d+',b))
        return numsA and numsB and numsA!=numsB

    # =========================================================
    # QUESTION ANSWERING
    # =========================================================

    # Intent detection keywords
    INTENT_KEYWORDS = {
        "post_termination": [
            "after termination", "post termination", "after leaving",
            "after resignation", "after employment", "once terminated",
            "after contract ends", "post-employment"
        ],
        "compensation": [
            "salary", "pay", "compensation", "wages", "payment",
            "bonus", "benefits", "remuneration"
        ],
        "termination": [
            "terminate", "termination", "end contract", "cancel",
            "cancellation", "firing", "dismissal"
        ],
        "confidentiality": [
            "confidential", "secret", "nda", "non-disclosure",
            "proprietary information", "trade secrets"
        ],
        "ip": [
            "intellectual property", "ip", "copyright", "patent",
            "trademark", "ownership", "work product"
        ],
        "liability": [
            "liability", "indemnity", "damages", "responsible",
            "accountable", "liable"
        ],
        "non_compete": [
            "non-compete", "non compete", "compete", "competition",
            "restrictive covenant", "solicitation"
        ]
    }

    # Intent to clause type mapping for boosting
    INTENT_BOOST_MAP = {
        "post_termination": ["confidentiality", "termination", "non-compete", "ip", "notice"],
        "compensation": ["salary", "bonus", "compensation", "benefits", "payment"],
        "termination": ["termination", "notice", "severance", "cause"],
        "confidentiality": ["confidentiality", "nda", "proprietary", "trade secrets"],
        "ip": ["intellectual property", "ip", "ownership", "work product"],
        "liability": ["liability", "indemnity", "limitation", "damages"],
        "non_compete": ["non-compete", "restrictive covenant", "solicitation"]
    }

    def _detect_intent(self, query: str) -> str:
        """
        Detect the intent/topic of a user's question.

        Args:
            query: User's question

        Returns:
            Intent category (e.g., 'post_termination', 'compensation', 'general')
        """
        q = query.lower()

        # Check each intent category
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(keyword in q for keyword in keywords):
                return intent

        return "general"

    def _rewrite_query_with_llm(self, query: str) -> str:
        """
        Use LLM to rewrite user question into a better search query.

        Args:
            query: Original user question

        Returns:
            Rewritten search query optimized for legal clause retrieval
        """
        rewrite_prompt = f"""Rewrite this question into a focused legal search query.

User Question: {query}

Instructions:
- Extract key legal concepts and obligations
- Focus on searchable clause types (e.g., confidentiality, termination, compensation)
- Include relevant timeframes (e.g., post-termination, during employment)
- Keep it concise (1-2 sentences max)
- Use legal terminology

Search Query:"""

        try:
            rewritten = self.llm.generate(rewrite_prompt, max_tokens=100, temperature=0.2)
            logger.info(f"Query rewritten: '{query}' → '{rewritten.strip()}'")
            return rewritten.strip()
        except Exception as e:
            logger.warning(f"Query rewriting failed: {e}, using original")
            return query

    def _rerank_results(self, results: List[Dict], intent: str, boost_factor: float = 0.15) -> List[Dict]:
        """
        Re-rank search results based on detected intent.

        Args:
            results: Initial search results
            intent: Detected intent category
            boost_factor: Score boost for matching clauses

        Returns:
            Re-ranked results with adjusted scores
        """
        boosted_clauses = self.INTENT_BOOST_MAP.get(intent, [])

        for result in results:
            original_score = result.get("similarity_score", 0.0)
            boost = 0.0

            clause_text = result.get("text", "").lower()
            clause_type = result.get("clause_type", "").lower()

            # Boost if clause type or text matches intent
            for keyword in boosted_clauses:
                if keyword in clause_text or keyword in clause_type:
                    boost += boost_factor
                    break

            result["adjusted_score"] = min(1.0, original_score + boost)

        # Sort by adjusted score
        return sorted(results, key=lambda x: x.get("adjusted_score", 0), reverse=True)

    def answer_question(self, question: str, vector_db, top_k: int = 5) -> Dict:
        """
        Answer a question using semantic search over the document clauses.
        
        Args:
            question: User's question about the contracts
            vector_db: Vector database collection with clause embeddings
            top_k: Number of relevant clauses to retrieve
            
        Returns:
            Dict with 'answer' and 'evidence' fields
        """
        logger.info(f"\n🔵 ANSWERING QUESTION: {question}")
        
        # CRITICAL: Use question directly for embedding (not rewriting)
        # Rewriting adds unnecessary complexity and can blur the query
        question_embedding = self.embeddings.embed_text(question)
        logger.info(f"✓ Generated embedding for question")
        
        # Search for relevant clauses with question embedding
        initial_results = vector_db.query(
            query_embedding=question_embedding,
            top_k=top_k * 2,  # Fetch 2x for potential filtering
            min_similarity=0.2  # Lower threshold before reranking
        )
        
        logger.info(f"✓ Retrieved {len(initial_results)} initial results from vector DB")
        if initial_results:
            logger.info(f"  Top result: {initial_results[0].get('clause_type', 'Unknown')} (score: {initial_results[0].get('similarity_score', 'N/A')})")
        
        # Detect intent for metadata filtering
        intent = self._detect_intent(question)
        logger.info(f"✓ Detected intent: {intent}")
        
        # Light filtering based on intent (but keep all results if intent is general)
        filtered_results = initial_results
        if intent != "general":
            boosted_types = self.INTENT_BOOST_MAP.get(intent, [])
            matching = [r for r in initial_results if any(
                bt in r.get("clause_type", "").lower() or bt in r.get("text", "").lower()
                for bt in boosted_types
            )]
            non_matching = [r for r in initial_results if r not in matching]
            filtered_results = matching + non_matching
            logger.info(f"✓ Intent-boosted: {len(matching)} matching, {len(non_matching)} other clauses")
        
        # Take top_k results
        results = filtered_results[:top_k]
        logger.info(f"✓ Final retrieval: {len(results)} clauses for answer generation")
        
        # Extract clauses and metadata
        evidence = []
        context_parts = []
        
        for i, result in enumerate(results, 1):
            evidence.append({
                "text": result.get("text", ""),
                "document": result.get("document_name", result.get("document_id", "Unknown")),
                "section": result.get("clause_type", "General"),
                "page": result.get("section", "N/A")
            })
            
            # Build context for LLM
            doc_name = result.get("document_name", result.get("document_id", "Unknown"))
            clause_type = result.get("clause_type", "General")
            text = result.get("text", "")
            context_parts.append(f"[{doc_name} - {clause_type}]: {text}")
            logger.info(f"  [{i}] {clause_type} from {doc_name}")
        
        # If no relevant clauses found
        if not context_parts:
            logger.warning("⚠️ No relevant clauses found for this question")
            return {
                "answer": "I couldn't find relevant information in the uploaded contracts to answer this question.",
                "evidence": []
            }
        
        # Build prompt for LLM (simple and question-focused)
        context = "\n\n".join(context_parts)
        prompt = f"""User Question:
{question}

Relevant Contract Clauses:
{context}

Answer the user's question clearly and directly based only on the evidence above.
Return JSON with: answer, why_it_matters, practical_impact, confidence
"""
        
        logger.info(f"✓ Built context with {len(context_parts)} clauses")
        logger.info(f"✓ Calling LLM with QA_SYSTEM_PROMPT for answer generation")
        
        # Generate answer using LLM with QA system prompt
        try:
            answer_text = self.llm.generate(
                prompt,
                max_tokens=500,
                temperature=0.3,
                system_prompt=self.llm.QA_SYSTEM_PROMPT,
            )
            
            logger.info(f"✓ LLM response received ({len(answer_text)} chars)")

            # Parse structured JSON response
            parsed = None
            try:
                parsed = json.loads(answer_text)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse JSON response: {e}")
                parsed = None
            
            if isinstance(parsed, dict) and "answer" in parsed:
                result_dict = {
                    "answer": parsed.get("answer", "").strip(),
                    "why_it_matters": parsed.get("why_it_matters", ""),
                    "practical_impact": parsed.get("practical_impact", ""),
                    "confidence": parsed.get("confidence", 0.5),
                    "evidence": evidence
                }
                logger.info(f"✓ Answer generated successfully\n")
                return result_dict
            else:
                # Fallback if JSON parsing fails
                logger.warning("⚠️ JSON parsing failed, returning raw response")
                return {
                    "answer": answer_text.strip(),
                    "why_it_matters": "",
                    "practical_impact": "",
                    "confidence": 0.5,
                    "evidence": evidence
                }
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"Error generating answer: {str(e)}",
                "evidence": evidence
            }
