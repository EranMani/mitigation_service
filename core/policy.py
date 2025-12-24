"""
This module provides a Policy class that loads policy rules from a JSON file
The policy will decide which action priority is best suitable for the prompt - block, redact or allow
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from .redactors import EmailRedactor, PhoneRedactor, SecretRedactor, CreditCardRedactor
from .semantic import SemanticBlocker

# Constants
POLICY_FILENAME = "policy.json"
DEFAULT_MAX_CHARS = 200

class Policy:
    """Manages policy rules loaded from a JSON file and assign the required action."""
    
    def __init__(self, policy_path: Optional[Path] = None):
        """Initialize the Policy instance by loading policy rules from a JSON file."""
        self.policy_file_path = Path(__file__).parent.parent / POLICY_FILENAME

        self.rules = {}
        self.redactors = {}
        self.semantic_blocker = None

        # Load the policy rules and setup redactors on startup
        self.load_policy()
        
    def load_policy(self):
        """Load rules and configure redactors. Can be called at runtime to reload."""
        try:
            with open(self.policy_file_path, "r", encoding="utf-8") as f:
                self.rules = json.load(f)
            
            print(f"Loaded {len(self.rules)} rules from {self.policy_file_path}")
            
            # Re-initialize redactors based on new config
            self._configure_components()
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # If we can't read the security rules, we must not start.
            print(f"CRITICAL SECURITY ERROR: Could not load {self.policy_file_path}")
            raise e

    def evaluate_prompt(self, prompt):
        """
        Main entry point. Evaluates a prompt against all active rules.
        1. Check Hard Blocks (Keywords, Length)
        2. Check Semantic Blocks (AI)
        3. Apply Redaction (PII)
        4. Allow (Default)
        """

        # 1. BLOCKING CHECK (Highest Priority)
        block_result = self._check_blocking(prompt)
        if block_result:
            return block_result

        # 2. SEMANTIC BLOCKING (AI, between medium and high priority)
        # Another layer of security 
        semantic_result = self._check_semantic_blocking(prompt)
        if semantic_result:
            return semantic_result

        # 3. REDACTION CHECK (Medium Priority)
        redact_result = self._apply_redaction(prompt)
        if redact_result:
            return redact_result

        # 4. ALLOW (Default)
        return {
            "action": "allow",
            "prompt_out": prompt,
            "reason": "Safe, no action required"
        }

    def _configure_components(self):
        """Instantiate redactors AND the semantic blocker."""
        # A. Setup Redactors
        config = self.rules.get("redaction_rules", {})
        self.redactors = {}

        redactor_map = {
            "redact_emails": ("Email", EmailRedactor),
            "redact_phone_numbers": ("Phone", PhoneRedactor),
            "redact_secrets": ("Secret", SecretRedactor),
            "redact_credit_cards": ("CreditCard", CreditCardRedactor),
        }

        for config_key, (name, cls) in redactor_map.items():
            if config.get(config_key, False):
                self.redactors[name] = cls()

        # B. Setup Semantic Blocker
        semantic_config = self.rules.get("semantic_blocking", {})
        if semantic_config.get("enabled", False):
            phrases = semantic_config.get("banned_phrases", [])
            threshold = semantic_config.get("threshold", 0.6)
            self.semantic_blocker = SemanticBlocker(phrases, threshold)
        else:
            self.semantic_blocker = None

        print(f"Active Redactors: {list(self.redactors.keys())}")
        print(f"Semantic Blocking: {'Enabled' if self.semantic_blocker else 'Disabled'}")
        
    def _apply_redaction(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Apply redactions to a prompt."""
        current_prompt = prompt
        affected_types = []

        # Run prompt through the active redactors
        for name, redactor in self.redactors.items():
            original_prompt = current_prompt
            current_prompt = redactor.redact_text(current_prompt)
            
            # If text changed, record which redactor did it
            if current_prompt != original_prompt:
                affected_types.append(name)

        # If any redaction happened, return the modified result
        if current_prompt != prompt:
            return {
                "action": "redact",
                "prompt_out": current_prompt,
                "reason": f"P.I.I. detected and redacted: {affected_types}"
            }
        
        return None

    def _check_semantic_blocking(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Check against the AI model."""
        if not self.semantic_blocker:
            return None

        # Send the prompt to the semantic model
        """
        NOTE: It returns a similarity score between the prompt and the banned phrases and if it is considered blocked or not
        How to check if a prompt is blocked => similarity score > threshold (can be configured in the policy.json file)
        """
        
        is_blocked, score = self.semantic_blocker.check_blocking(prompt)
        
        # The AI model response
        if is_blocked:
            return {
                "action": "block",
                "prompt_out": prompt,  # We return original prompt (but blocked)
                "reason": f"Semantic Policy Violation (Similarity: {score:.2f})"
            }

        # None means the AI model sees nothing wrong with the prompt
        return None

    def _check_blocking(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Check if a prompt contains any blocked keywords."""

        # Check 1: Length
        max_prompt_chars = self.rules.get("max_prompt_chars", DEFAULT_MAX_CHARS)
        if len(prompt) > max_prompt_chars:
            return {
                "action": "block",
                "prompt_out": prompt,
                "reason": f"Prompt is too long. Max length is {max_prompt_chars} characters."
            }

        # Check 2: Banned Keywords
        prompt_lower = prompt.lower()
        found_blocked_keywords = [
            keyword for keyword in self.rules["banned_keywords"] 
            if keyword.lower() in prompt_lower  
        ]

        if found_blocked_keywords:
            return {
                "action": "block",
                "prompt_out": prompt,
                "reason": f"Contains banned keywords: {found_blocked_keywords}"
            }

        return None


if __name__ == "__main__":
    # Run this in terminal -> python -m core.policy
    policy = Policy()
    print(policy.evaluate_prompt("my email is test@example.com and my phone number is 1234567890"))
    print(policy.evaluate_prompt("My name is John Doe and my api key is SECRET{1234567890}"))
    print(policy.evaluate_prompt("i woke up in the morning and ate breakfast"))
    print(policy.evaluate_prompt("I hate youUUUUU and i want to KILl someone"))