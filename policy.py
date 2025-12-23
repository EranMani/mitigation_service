"""
This module provides a Policy class that loads policy rules from a JSON file
The policy will decide which action priority is best suitable for the prompt - block, redact or allow
"""

import json
from pathlib import Path
from redactors import EmailRedactor, PhoneRedactor, SecretRedactor, CreditCardRedactor

POLICY_FILE_PATH = Path(__file__).parent / "policy.json"

class Policy:
    """Manages policy rules loaded from a JSON file and assign the required action."""
    
    def __init__(self, policy_file_path=POLICY_FILE_PATH):
        """Initialize the Policy instance by loading policy rules from a JSON file."""
        self.policy_file_path = policy_file_path

        # Load the policy rules and setup redactors
        self.load_policy()
        
    def load_policy(self):
        """Load the rules and setup redactors. Can also be used to reload the policy when needed."""
        with open(self.policy_file_path, "r") as policy_rules:
            self.rules = json.load(policy_rules)
        print(f"Loaded {len(self.rules)} policy rules from {self.policy_file_path}")

        self.redactors = self.configure_redactors()
        print(f"Initialized the following redactors: {[redactor for redactor in self.redactors.keys()]}")    

    def eval(self, prompt):
        """Evaluate the prompt and decide which action should be taken."""
        pass

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
        for redactor in self.redactors.values():
            # Pass the prompt and process it for each redactor
            redacted_prompt = redactor.redact_text(redacted_prompt)

        return redacted_prompt

    def is_blocked(self, prompt):
        """Check if a prompt contains any blocked keywords."""
        found_blocked_keywords = [keyword for keyword in self.rules["banned_keywords"] if keyword in prompt.lower()]
        if found_blocked_keywords:
            print(f"Found blocked keywords: {found_blocked_keywords}")
            return True
        else:
            return False

if __name__ == "__main__":
    policy = Policy()
    print(policy.is_blocked("I hate you and i want to kill myself"))
    print(policy.is_redacted("my email is test@example.com and my phone number is 1234567890"))