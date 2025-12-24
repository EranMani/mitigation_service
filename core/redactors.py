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
