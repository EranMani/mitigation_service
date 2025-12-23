"""
This module provides a Policy class that loads policy rules from a JSON file
The policy will decide which action priority is best suitable for the prompt - block, redact or allow
"""

import json
from pathlib import Path
from core.redactors import EmailRedactor, PhoneRedactor, SecretRedactor, CreditCardRedactor

POLICY_FILE_PATH = Path(__file__).parent.parent / "policy.json"

class Policy:
    """Manages policy rules loaded from a JSON file and assign the required action."""
    
    def __init__(self, policy_file_path=POLICY_FILE_PATH):
        """Initialize the Policy instance by loading policy rules from a JSON file."""
        self.policy_file_path = policy_file_path

        # Load the policy rules and setup redactors
        self.load_policy()
        
    def load_policy(self):
        """Load the rules and setup redactors. Can also be used to reload the policy when needed."""
        try:
            # Load policy rules
            with open(self.policy_file_path, "r") as policy_rules:
                self.rules = json.load(policy_rules)
            print(f"Loaded {len(self.rules)} policy rules from {self.policy_file_path}")

            self.redactors = self.configure_redactors()
            print(f"Initialized the following redactors: {[redactor for redactor in self.redactors.keys()]}")    

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"CRITICAL SECURITY ERROR!!!")
            print(f"Could not load policy file: {self.policy_file_path}")
            print(f"Error details: {e}")
            print(f"Server cannot start without valid rules. Exiting...")
            raise e

    def evaluate_prompt(self, prompt):
        """Evaluate the prompt and decide which action should be taken."""

        # Check prompt for blocked rules
        is_blocked = self.is_blocked(prompt)
        if is_blocked:
            return {
                "action": is_blocked["action"],
                "prompt_out": prompt,
                "reason": is_blocked["reason"]
            }

        # Check prompt for PII data
        is_redacted = self.is_redacted(prompt)
        if is_redacted:
            return {
                "action": is_redacted["action"],
                "prompt_out": is_redacted["prompt_out"],
                "reason": is_redacted["reason"]
            }

        # Prompt is safe
        return {
            "action": "allow",
            "prompt_out": prompt,
            "reason": "Safe, no action required"
        }

    def configure_redactors(self):
        """Configure the redactors based on the policy config toggles."""
        redaction_config = self.rules.get("redaction_rules", {})
        redactors = {}

        if redaction_config.get("redact_emails", False):
            redactors["email"] = EmailRedactor()
        if redaction_config.get("redact_phone_numbers", False):
            redactors["phone"] = PhoneRedactor()
        if redaction_config.get("redact_secrets", False):
            redactors["secret"] = SecretRedactor()
        if redaction_config.get("redact_credit_cards", False):
            redactors["credit_card"] = CreditCardRedactor()

        return redactors
        
    def is_redacted(self, prompt):
        """Check if a prompt contains any redacted information."""
        # Start with the original prompt
        redacted_prompt = prompt

        # List to store used redactors
        redacted_categories = []

        for redactor in self.redactors.values():
            # Save prompt state before running redactor on it
            previous_prompt = redacted_prompt

            # Pass the prompt and process it for each redactor
            redacted_prompt = redactor.redact_text(redacted_prompt)

            if redacted_prompt != previous_prompt:
                category_name = type(redactor).__name__.replace("Redactor", "")
                redacted_categories.append(category_name)

        if redacted_prompt != prompt:
            return {
                "action": "redact",
                "prompt_out": redacted_prompt,
                "reason" : f"P.I.I detected and redacted: {redacted_categories}"
            }
        else:
            return {}

    def is_blocked(self, prompt):
        """Check if a prompt contains any blocked keywords."""
        found_blocked_keywords = [keyword for keyword in self.rules["banned_keywords"] if keyword.lower() in prompt.lower()]

        # Check if the prompt is too long
        max_prompt_chars = self.rules.get("max_prompt_chars", 1000)
        if len(prompt) > max_prompt_chars:
            return {"action": "block", "reason": f"Prompt is too long. Max length is {max_prompt_chars} characters."}
            
        if found_blocked_keywords:
            return {"action": "block", "reason": f"Found blocked keywords: {found_blocked_keywords}"}
        
        return {}

if __name__ == "__main__":
    policy = Policy()
    # print(policy.is_blocked("I hate you and i want to kill myself"))
    # print(policy.is_redacted("my email is test@example.com and my phone number is 1234567890"))
    print(policy.evaluate_prompt("My name is John Doe and my api key is SECRET{1234567890}"))
    print(policy.evaluate_prompt("i woke up in the morning and ate breakfast"))
    print(policy.evaluate_prompt("I hate youUUUUU and i want to KILL myself"))