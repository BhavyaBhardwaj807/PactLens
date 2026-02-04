"""
PactLens Backend - LLM Service
Wrapper for Google Gemini API calls with fallbacks
"""

import os
import json
from typing import Optional
import time


class LLMService:
    """Service for LLM-powered analysis using Google Gemini"""
    
    # Production-grade system prompt for Indian law contract analysis
    SYSTEM_PROMPT = """You are PactLens, an AI system designed to analyze contracts strictly under INDIAN LAW.

LEGAL SCOPE CONSTRAINTS (MANDATORY):
- You MUST base all legal reasoning, interpretations, risks, and recommendations ONLY on laws applicable in India.
- You MUST NOT reference, imply, or rely on:
  - United States law
  - United Kingdom law
  - European Union law
  - International law or treaties unless they are explicitly adopted and enforceable in India.
- If a clause appears to rely on foreign jurisdiction or non-Indian legal principles, you MUST explicitly state that it may be unenforceable or unclear under Indian law.

ROLE & TONE:
- You are NOT a lawyer.
- You provide informational analysis only, not legal advice.
- Explain concepts in plain English for a non-legal audience.
- Avoid legal jargon unless absolutely necessary, and explain it when used.

CONTRADICTION ANALYSIS RULES:
- When comparing clauses:
  - Focus on semantic meaning, obligations, rights, timelines, penalties, and exclusions.
  - Identify conflicts as:
    - "direct" (clearly opposing obligations)
    - "partial" (conflicting in some scenarios)
    - "ambiguous" (unclear or context-dependent)
- Always assess risk from the perspective of Indian enforceability.

INDIAN LAW CONTEXT REQUIREMENTS:
- When applicable, reason using broadly recognized Indian legal principles such as:
  - Indian Contract Act, 1872
  - principles of reasonableness, consent, consideration, and public policy
- If no clear Indian legal position exists:
  - explicitly say so
  - mark the risk as "ambiguous"

SAFETY & DISCLAIMER (MANDATORY):
- Always include or assume this disclaimer:
  "This analysis is for informational purposes only and does not constitute legal advice under Indian law."
- If a contradiction or clause poses medium or high risk:
  - recommend consulting a qualified lawyer practicing in India.

OUTPUT FORMAT:
- ALWAYS respond in valid JSON only.
- Do NOT include explanations outside the JSON.
- Ensure all required fields are present and correctly typed.

FAIL-SAFE BEHAVIOR:
- If the request requires non-Indian legal reasoning:
  - refuse politely
  - explain that PactLens is restricted to Indian law only.
"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        """
        Initialize LLM service
        
        Args:
            api_key: Google Gemini API key
            model: Model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai
            except ImportError:
                print("Warning: google-generativeai library not installed. Using mock responses.")
    
    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """
        Generate response from LLM with Indian law system prompt
        
        Args:
            prompt: Input prompt
            temperature: Creativity level (0-1)
            
        Returns:
            Generated text
        """
        if self.client:
            try:
                model = self.client.GenerativeModel(
                    self.model,
                    system_instruction=self.SYSTEM_PROMPT
                )
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 2048,
                    }
                )
                return response.text
            except Exception as e:
                print(f"LLM Error: {e}")
                return self._get_mock_response(prompt)
        else:
            return self._get_mock_response(prompt)
    
    def _get_mock_response(self, prompt: str) -> str:
        """Provide mock responses for development/testing (follows Indian law constraints)"""
        
        # Check if this is a batch contradiction request (looks for "PAIR X" pattern)
        if "pair" in prompt.lower() and "[" in prompt and "]" in prompt:
            # Extract pair IDs from prompt to generate matching responses
            import re
            pair_ids = re.findall(r"pair\s+(\d+)", prompt.lower())
            pair_ids = [int(pid) for pid in pair_ids] if pair_ids else [1]
            
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
                    "indian_law_context": "Under the Indian Contract Act, 1872, non-compete and confidentiality clauses are enforceable only if reasonable in scope and duration. The conflicting terms may be challenged under principles of reasonableness and public policy.",
                    "recommendations": [
                        "Clarify which document takes precedence",
                        "Consider non-compete clause limitations under Indian law (typically 2-3 years maximum)",
                        "Consult a qualified lawyer practicing in India"
                    ],
                    "requires_lawyer": True
                })
            return json.dumps(results)
        
        # Single contradiction analysis (not batch)
        if "contradiction" in prompt.lower() or "contradict" in prompt.lower():
            return json.dumps({
                "has_contradiction": True,
                "contradiction_type": "partial",
                "risk_level": "medium",
                "summary": "Partial conflict found between confidentiality terms",
                "explanation": "Document A restricts disclosure indefinitely, while Document B allows disclosure after 2 years. This creates ambiguity about post-employment obligations.",
                "indian_law_context": "Under the Indian Contract Act, 1872, non-compete and confidentiality clauses are enforceable only if reasonable in scope and duration. The conflicting terms may be challenged under principles of reasonableness and public policy.",
                "recommendations": [
                    "Clarify which document takes precedence",
                    "Consider non-compete clause limitations under Indian law (typically 2-3 years maximum)",
                    "Consult a qualified lawyer practicing in India"
                ],
                "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law."
            })
        
        elif "answer" in prompt.lower() or "question" in prompt.lower():
            return json.dumps({
                "answer": "Based on the contracts, this appears to be a shared obligation across both documents. Under Indian law, the enforceability depends on the specific terms and context.",
                "confidence": 0.7,
                "requires_lawyer": True,
                "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law."
            })
        
        return json.dumps({
            "answer": "This requires more specific information. Please note that PactLens analyzes contracts strictly under Indian law.",
            "confidence": 0.3,
            "requires_lawyer": True,
            "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice under Indian law."
        })


class EmbeddingsService:
    """Service for generating text embeddings using Google Gemini"""
    
    def __init__(self, api_key: str, model: str = "models/embedding-001"):
        """
        Initialize embeddings service
        
        Args:
            api_key: Google Gemini API key
            model: Embedding model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai
            except ImportError:
                print("Warning: google-generativeai library not installed. Using mock embeddings.")
    
    def embed_text(self, text: str) -> list:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.client:
            try:
                result = self.client.embed_content(
                    model=self.model,
                    content=text[:8191],  # Limit to max tokens
                )
                return result['embedding']
            except Exception as e:
                print(f"Embedding Error: {e}")
                return self._get_mock_embedding(text)
        else:
            return self._get_mock_embedding(text)
    
    def embed_batch(self, texts: list) -> list:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed_text(text))
            # Rate limiting
            time.sleep(0.01)
        return embeddings
    
    def _get_mock_embedding(self, text: str) -> list:
        """
        Generate semantic mock embedding based on text keywords.
        Similar texts will have higher cosine similarity.
        """
        import re
        
        # Extract keywords and normalize
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Create keyword-based features
        keywords = [
            'confidential', 'disclosure', 'terminate', 'termination', 'payment', 
            'liability', 'indemnity', 'warranty', 'breach', 'notice', 'days',
            'agreement', 'party', 'parties', 'obligations', 'rights', 'shall',
            'compensation', 'damages', 'dispute', 'arbitration', 'jurisdiction',
            'intellectual', 'property', 'ownership', 'transfer', 'assignment',
            'non-compete', 'non-disclosure', 'employment', 'contractor', 'vendor',
            'purchase', 'sale', 'delivery', 'service', 'product', 'license'
        ]
        
        # Count keyword occurrences
        keyword_counts = {kw: words.count(kw) for kw in keywords}
        
        # Also extract numbers (for payment amounts, durations, etc.)
        numbers = re.findall(r'\d+', text)
        avg_number = sum(int(n) for n in numbers[:5]) / max(len(numbers[:5]), 1) if numbers else 0
        
        # Build embedding vector (384 dimensions for faster computation)
        embedding = []
        
        # Add keyword-based dimensions
        for kw in keywords:
            count = keyword_counts.get(kw, 0)
            # Normalize count to [0, 1] range with diminishing returns
            normalized = min(count / 5.0, 1.0)
            embedding.append(normalized)
        
        # Add text length feature
        embedding.append(min(len(text) / 1000.0, 1.0))
        
        # Add average number feature (normalized)
        embedding.append(min(avg_number / 1000.0, 1.0))
        
        # Pad to 384 dimensions with small random noise for uniqueness
        import random
        import hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        while len(embedding) < 384:
            embedding.append(random.random() * 0.1)  # Small random component
        
        # Normalize to unit vector
        norm = sum(x**2 for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
