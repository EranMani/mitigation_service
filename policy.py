"""
This module provides a Policy class that loads policy rules from a JSON file
"""

import json
from pathlib import Path
from redactors import EmailRedactor, PhoneRedactor, SecretRedactor, CreditCardRedactor

POLICY_FILE_PATH = Path(__file__).parent / "policy.json"

class Policy:
    """Manages policy rules loaded from a JSON file and assign the required action."""
    
    def __init__(self, policy_file_path):
        """Initialize the Policy instance by loading policy rules from a JSON file."""
        with open(policy_file_path, "r") as policy_rules:
            self.rules = json.load(policy_rules)
            print(f"Loaded {len(self.rules)} policy rules from {policy_file_path}")

        # Initialize redactors based on the policy config toggles
        self.redactors = self.configure_redactors()
        print(f"Initialized the following redactors: {[redactor for redactor in self.redactors.keys()]}")       


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
        

    def is_blocked(self, prompt):
        """Check if a prompt contains any blocked keywords."""
        found_blocked_keywords = [keyword for keyword in self.rules["banned_keywords"] if keyword in prompt.lower()]
        if found_blocked_keywords:
            print(f"Found blocked keywords: {found_blocked_keywords}")
            return True
        else:
            return False

if __name__ == "__main__":
    policy = Policy(POLICY_FILE_PATH)
    print(policy.is_blocked("I hate you and i want to kill myself"))