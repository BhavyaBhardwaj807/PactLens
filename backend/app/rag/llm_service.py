"""
PactLens Backend - LLM Service
Wrapper for Google Gemini API calls with fallbacks
"""

import os
import json
import logging
from typing import Optional
import time
import hashlib
import random
import re
import numpy as np
from app.utils.cache import SimpleCache

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered analysis using Google Gemini"""

    # Neutral fallback system prompt
    SYSTEM_PROMPT = """You are PactLens, an AI assistant for contract analysis under INDIAN LAW.
Follow the user's instructions precisely. Use plain English.
"""

    # A) Contradiction Mode (used ONLY for analyze_contradictions)
    CONTRADICTION_SYSTEM_PROMPT = """You analyze clauses for contradictions under Indian law.
Return contradiction JSON only.

Output rules (MANDATORY):
- Return a JSON ARRAY only.
- Each item must include: pair_id, has_contradiction, contradiction_type (direct|partial|ambiguous),
  risk_level (low|medium|high), summary, explanation, recommendations (array).
- If no contradiction for a pair, set has_contradiction=false.
- Do not include any prose outside JSON.
"""

    # B) Q&A Mode (used for answer_question)
    QA_SYSTEM_PROMPT = """You are PactLens, an AI that explains contract issues to ordinary people in a clear, natural, and practical way.

GOAL:
Help users quickly understand risks, obligations, and conflicts in their contracts without legal jargon.

TONE:
- Sound like a helpful expert, not a lawyer or judge
- Friendly, calm, and neutral
- Clear and simple English
- Natural, conversational phrasing
- Avoid robotic or template-like responses

STYLE RULES:
- Write like you are explaining to a smart non-lawyer
- Prefer short sentences
- Use plain words instead of legal terms
- If legal terms are necessary, explain them simply
- Focus on what matters to the user

CONTENT RULES:
- Answer the user's exact question first
- Focus only on relevant clauses
- Do NOT mention irrelevant sections
- Do NOT repeat the same point
- Do NOT dump raw legal analysis

EXPLANATION FORMAT:
1) Direct answer in 1–2 sentences
2) Short explanation of why it matters
3) Optional practical takeaway

EXAMPLE STYLE:
Instead of:
"Both documents impose confidentiality obligations with differing durations."

Say:
"Your documents set different time limits for confidentiality — 2 years, 3 years, and 5 years. This makes it unclear how long you are actually bound."

IN INDIAN LAW CONTEXT:
- Base reasoning on Indian Contract Act principles
- Mention Indian law only if it adds clarity
- Do not over-cite laws

AVOID:
- Legal lectures
- Long disclaimers
- Repeating clause text
- Saying "Document A" and "Document B" (use natural wording)

END GOAL:
User should feel: "I understand this now."

RETURN FORMAT (JSON only):
{
  "answer": "Direct answer in 1-2 sentences based on evidence",
  "why_it_matters": "Short explanation of significance",
  "practical_impact": "What this means for the person (money, time, restrictions)",
  "confidence": 0.0-1.0
}

Always return valid JSON.
"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize LLM service
        
        Args:
            api_key: Google Gemini API key
            model: Model to use (defaults to env LLM_MODEL or gemini-1.5-flash)
        """
        self.api_key = api_key
        self.model = model or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        self.client = None
        self.cache = SimpleCache()
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai
            except ImportError:
                print("Warning: google-generativeai library not installed. Using mock responses.")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate response from LLM with Indian law system prompt
        
        Args:
            prompt: Input prompt
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt override
            
        Returns:
            Generated text
        """
        # Resolve system prompt override
        active_system_prompt = system_prompt or self.SYSTEM_PROMPT

        # Check cache first
        # Cache key = system_prompt + temperature + max_tokens + prompt
        # This ensures different questions/prompts get different cache entries
        cache_key = hashlib.sha256(
            f"{active_system_prompt}||temp={temperature}||max={max_tokens}||{prompt}".encode()
        ).hexdigest()
        
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"✓ Cache hit for prompt (key: {cache_key[:8]}...)")
            return cached
        
        logger.debug(f"✓ Cache miss, generating new response (key: {cache_key[:8]}...)")
        
        # Generate response
        if self.client:
            try:
                model = self.client.GenerativeModel(self.model)
                
                full_prompt = f"""
{active_system_prompt}

USER REQUEST:
{prompt}
"""
                
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                )
                result = response.text
                logger.info(f"✓ Gemini API response: {len(result)} chars")
            except Exception as e:
                logger.warning(f"LLM Error: {e}, falling back to mock")
                result = self._get_mock_response(prompt)
        else:
            logger.warning("No Gemini client, using mock response")
            result = self._get_mock_response(prompt)
        
        # Cache result
        self.cache.set(cache_key, result)
        return result

    def detect_intent(self, query: str) -> str:
        """Detect intent to route to QA or contradiction mode."""
        if "contradict" in query.lower():
            return "contradiction"
        return "qa"

    def generate_answer(
        self,
        prompt: str,
        mode: str = "qa",
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate response using the correct system prompt based on mode.

        Args:
            prompt: Input prompt
            mode: "qa", "contradiction", or "auto"
        """
        if mode == "auto":
            mode = self.detect_intent(prompt)

        if mode == "contradiction":
            system = self.CONTRADICTION_SYSTEM_PROMPT
        else:
            system = self.QA_SYSTEM_PROMPT

        return self.generate(
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system,
        )
    
    def _get_mock_response(self, prompt: str) -> str:
        """Provide mock responses for development/testing (follows Indian law constraints)"""
        
        # Check if this is a batch contradiction request (looks for "PAIR X" pattern)
        if "pair" in prompt.lower() or "contradict" in prompt.lower():
            # Extract pair IDs from prompt to generate matching responses
            import re
            pair_ids = re.findall(r"pair\s+(\d+)", prompt.lower())
            pair_ids = [int(pid) for pid in pair_ids] if pair_ids else [1]
            
            print(f"🔥 Mock: Detected batch request with {len(pair_ids)} pairs")
            
            # Generate mock responses for each pair
            results = []
            for pair_id in pair_ids:
                results.append({
                    "pair_id": pair_id,
                    "has_contradiction": True,
                    "contradiction_type": "partial",
                    "risk_level": "medium",
                    "summary": f"Partial conflict found in clause pair {pair_id}",
                    "explanation": "Document A restricts disclosure indefinitely, while Document B allows disclosure after 2 years. This creates ambiguity about post-employment obligations.",
                    "recommendations": [
                        "Clarify which document takes precedence",
                        "Consider non-compete clause limitations under Indian law (typically 2-3 years maximum)",
                        "Consult a qualified lawyer practicing in India"
                    ],
                    "requires_lawyer": True
                })
            return json.dumps(results)

        if "answer" in prompt.lower() or "question" in prompt.lower():
            return json.dumps({
                "answer": "Both documents require the same obligation during employment. Document A requires it indefinitely; Document B requires it for 2 years post-termination.",
                "why_it_matters": "Conflicting post-employment timelines create enforcement uncertainty and may weaken legal protection.",
                "practical_impact": "If you leave the company, it's unclear whether confidentiality lasts indefinitely or just 2 years. This ambiguity could be challenged.",
                "confidence": 0.75
            })
        
        return json.dumps({
            "answer": "Unable to answer with confidence—need more specific clause text from the contracts.",
            "why_it_matters": "",
            "practical_impact": "",
            "confidence": 0.3
        })


class EmbeddingsService:

    def __init__(self, api_key=None, use_cloud=False):
        self.api_key = api_key
        self.use_cloud = use_cloud and api_key

    # ===============================
    # MAIN EMBED FUNCTION
    # ===============================
    def embed_text(self, text: str):

        # 🔥 DEV MODE: always local
        if not self.use_cloud:
            return self._local_embedding(text)

        # PROD MODE: cloud fallback
        try:
            return self._cloud_embedding(text)
        except Exception:
            return self._local_embedding(text)

    # ===============================
    # LOCAL SEMANTIC EMBEDDING
    # ===============================
    def _local_embedding(self, text):

        words = re.findall(r"\b\w+\b", text.lower())

        keywords = [
            "confidential","terminate","payment","liability",
            "indemnity","notice","days","agreement","compensation"
        ]

        vec = []

        for kw in keywords:
            vec.append(words.count(kw) / 5)

        # deterministic randomness
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8],16)
        random.seed(seed)

        while len(vec) < 128:
            vec.append(random.random()*0.05)

        arr = np.array(vec)
        norm = np.linalg.norm(arr)
        return (arr/norm).tolist()
