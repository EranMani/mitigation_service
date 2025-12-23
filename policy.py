"""
This module provides a Policy class that loads policy rules from a JSON file
"""

import json
from pathlib import Path

POLICY_FILE_PATH = Path(__file__).parent / "policy.json"

class Policy:
    """Manages policy rules loaded from a JSON file and assign the required action."""
    
    def __init__(self, policy_file_path):
        """Initialize the Policy instance by loading policy rules from a JSON file."""
        with open(policy_file_path, "r") as policy_rules:
            self.rules = json.load(policy_rules)
            print(f"Loaded {len(self.rules)} policy rules from {policy_file_path}")

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