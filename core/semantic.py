import os
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class SemanticBlocker:
    """
    Checks if the prompt is semantically similar to banned phrases using AI.
    """
    def __init__(self, banned_phrases, threshold=0.6):
        self.banned_phrases = banned_phrases
        self.threshold = threshold
        self.model = None
        self.encoded_banned = None

        if not HAS_TRANSFORMERS:
            print("[WARN] Sentence Transformers not installed. Semantic blocking disabled.")
            return

        # Check for offline model
        local_model_path = "/app/models/all-MiniLM-L6-v2"
        
        try:
            if os.path.exists(local_model_path):
                print(f"Loading offline model from {local_model_path}...")
                self.model = SentenceTransformer(local_model_path)
            else:
                print("Offline model not found. Trying internet download...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')

            self.encoded_banned = self.model.encode(self.banned_phrases, convert_to_tensor=True)
            print("Semantic Model Loaded Successfully.")
            
        except Exception as e:
            print(f"[ERROR] Failed to load AI model: {e}")
            self.model = None

    def check_blocking(self, text):
        """
        Checks if text should be blocked.
        Returns: (is_blocked: bool, score: float)
        """
        if self.model is None or self.encoded_banned is None:
            return False, 0.0

        prompt_embedding = self.model.encode(text, convert_to_tensor=True)
        cosine_scores = util.cos_sim(prompt_embedding, self.encoded_banned)
        best_match_score = float(cosine_scores.max())

        if best_match_score > self.threshold:
            return True, best_match_score
        
        return False, best_match_score