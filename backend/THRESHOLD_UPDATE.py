# APPLY THESE CHANGES MANUALLY

# ===================================================================
# FILE 1: backend/app/config.py
# ===================================================================
# AFTER LINE 36 (after "top_k_similar: int = 5"), ADD:

    # Similarity threshold for LLM gating (only send high-confidence pairs to LLM)
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    # Values: 0.60 (low), 0.75 (medium), 0.85 (high), 0.90 (very high)

# ===================================================================
# FILE 2: backend/app/rag/pipeline.py  
# ===================================================================
# AFTER LINE 14 (after "from json import JSONDecodeError"), ADD:

from app.config import settings

# -------------------------------------------------------------------
# IN analyze_contradictions METHOD, AFTER "llm_calls = 0", ADD:

        pairs_filtered = 0  # Track how many pairs filtered by threshold
        
        # Get configurable similarity threshold from settings
        SIMILARITY_THRESHOLD = settings.similarity_threshold

# -------------------------------------------------------------------
# AFTER "print(f"Grouped by type: ...")", ADD:

        print(f"⚙️  Similarity threshold: {SIMILARITY_THRESHOLD:.2f} (only pairs ≥ this sent to LLM)")

# -------------------------------------------------------------------
# REPLACE THE SECTION:
#     # 🚀 OPTIMIZATION 4: Similarity threshold filtering
#     # Only compare clauses with >60% similarity
#     high_similarity_clauses = [
#         c for c in similar_clauses 
#         if c.get("similarity_score", 0) > 0.60
#     ]
# WITH:

                # 🚀 OPTIMIZATION 4: Similarity threshold gate (configurable)
                # Only send high-confidence pairs to LLM (reduces costs and latency)
                before_filter = len(similar_clauses)
                high_similarity_clauses = [
                    c for c in similar_clauses 
                    if c.get("similarity_score", 0) >= SIMILARITY_THRESHOLD
                ]
                filtered_count = before_filter - len(high_similarity_clauses)
                pairs_filtered += filtered_count
                
                if not high_similarity_clauses:
                    if before_filter > 0:
                        print(f"  ⏭️  Filtered {before_filter} pairs (all below {SIMILARITY_THRESHOLD:.2f} threshold)")
                    continue
                
                if filtered_count > 0:
                    print(f"  🔍 Found {before_filter} similar clauses, {filtered_count} filtered, {len(high_similarity_clauses)} sent to LLM")
                else:
                    print(f"  ✅ Found {len(high_similarity_clauses)} high-similarity matches (≥{SIMILARITY_THRESHOLD:.2f})")

# -------------------------------------------------------------------
# IN self.metrics.update(), ADD "pairs_filtered": pairs_filtered,

        self.metrics.update({
            "clauses_processed": len(clauses),
            "vector_searches": vector_searches,
            "llm_calls": llm_calls,
            "pairs_filtered": pairs_filtered,  # ADD THIS LINE
        })

# -------------------------------------------------------------------
# REPLACE FINAL PRINT SECTION WITH:

        # Calculate efficiency metrics
        potential_llm_calls = vector_searches * 3  # Estimate if no filtering
        saved_calls = pairs_filtered
        efficiency = (saved_calls / potential_llm_calls * 100) if potential_llm_calls > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"📊 ANALYSIS COMPLETE")
        print(f"   Clauses: {len(clauses)} | Searches: {vector_searches}")
        print(f"   Pairs filtered: {pairs_filtered} (≥{SIMILARITY_THRESHOLD:.2f} threshold)")
        print(f"   LLM calls: {llm_calls} | Efficiency: {efficiency:.1f}% saved")
        print(f"   Contradictions found: {len(contradictions)}")
        print(f"{'='*60}\n")

# ===================================================================
# FILE 3: backend/.env (OPTIONAL - to customize threshold)
# ===================================================================
# ADD:

# Similarity threshold for LLM calls (0.60-0.95)
SIMILARITY_THRESHOLD=0.75

# ===================================================================
# WHAT THIS DOES
# ===================================================================
# 1. Makes threshold configurable via environment variable
# 2. Filters clause pairs BEFORE sending to LLM
# 3. Only pairs with similarity ≥ 0.75 (default) are analyzed
# 4. Logs how many pairs were filtered out
# 5. Shows efficiency savings in final report

# EXAMPLE OUTPUT:
# ⚙️  Similarity threshold: 0.75 (only pairs ≥ this sent to LLM)
# 🔍 Found 5 similar clauses, 3 filtered, 2 sent to LLM
# ⏭️  Filtered 4 pairs (all below 0.75 threshold)
# 📊 ANALYSIS COMPLETE
#    Pairs filtered: 23 (≥0.75 threshold)
#    LLM calls: 12 | Efficiency: 65.7% saved
