"""
This module provides various redactor classes that can identify and replace
sensitive data like emails, phone numbers, secrets, and credit card numbers
with placeholder tags.

# NOTE: A redactor is a component (or function / middleware) whose job is to remove, mask, or replace sensitive data before it is
logged
returned in an API response
sent to another service
stored (logs, traces, metrics, DB)
It is a privacy & security filter that sits in the data flow.
"""

import re
import os
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class Redactor:
    """Base class for text redaction operations."""
    
    def redact_text(self, text):
        """Redact sensitive information from text. Base implementation returns text unchanged."""
        return text

class EmailRedactor(Redactor):
    """Redactor for email addresses in text."""
    
    def redact_text(self, text):
        """Replace email addresses with <EMAIL> placeholder."""
        return re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "<EMAIL>", text)

class PhoneRedactor(Redactor):
    """Redactor for phone numbers in text."""
    
    def redact_text(self, text):
        """Replace phone numbers (e.g., 123-456-7890) with <PHONE> placeholder."""
        return re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "<PHONE>", text)

class SecretRedactor(Redactor):
    """Redactor for secret values in SECRET{...} format."""
    
    def redact_text(self, text):
        """Replace SECRET{...} patterns with <SECRET> placeholder."""
        return re.sub(r'SECRET\{[^}]*\}', "<SECRET>", text)

class CreditCardRedactor(Redactor):
    """Redactor for credit card numbers in text."""
    
    def redact_text(self, text):
        """Replace credit card numbers (13-16 digits) with <CARD> placeholder."""
        return re.sub(r"\b(?:\d[ -]*?){13,16}\b", "<CARD>", text)


class SemanticRedactor(Redactor):
    """
    Uses an AI model to check if the prompt is semantically similar to banned phrases.
    """
    def __init__(self, banned_phrases, threshold=0.7):
        self.banned_phrases = banned_phrases
        self.threshold = threshold
        self.model = None
        self.encoded_banned = None

        if not HAS_TRANSFORMERS:
            print("[WARN] Sentence Transformers not installed. Semantic blocking disabled.")
            return

        # Check if we have the pre-downloaded model
        local_model_path = "/app/models/all-MiniLM-L6-v2"
        
        try:
            if os.path.exists(local_model_path):
                print(f"Loading offline model from {local_model_path}...")
                self.model = SentenceTransformer(local_model_path)
            else:
                # Fallback (Should not happen in Docker)
                print("Offline model not found. Trying internet download...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')

            # Pre-calculate embeddings for the banned phrases (Optimization)
            self.encoded_banned = self.model.encode(self.banned_phrases, convert_to_tensor=True)
            print("Semantic Model Loaded Successfully.")
            
        except Exception as e:
            print(f"[ERROR] Failed to load AI model: {e}")
            self.model = None

    def redact_text(self, text):
        """
        Returns the text IF safe. 
        Returns a BLOCKED message if it matches a banned concept.
        """
        # FIX: Check explicitly for None to avoid Tensor ambiguity error
        if self.model is None or self.encoded_banned is None:
            return text

        # Encode the incoming user prompt
        prompt_embedding = self.model.encode(text, convert_to_tensor=True)

        # Compare against all banned phrases
        cosine_scores = util.cos_sim(prompt_embedding, self.encoded_banned)

        # Check if any score is above the threshold
        best_match_score = float(cosine_scores.max())

        print(f"DEBUG: Score for '{text}' is {best_match_score}")

        if best_match_score > self.threshold:
            return f"[BLOCKED] Content violates policy (Similarity: {best_match_score:.2f})"
        
        return text