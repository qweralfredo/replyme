import pytest
from pydantic import ValidationError
from src.services.ai_classifier import EmailClassification

def test_email_classification_validation():
    # Test that invalid data raises a validation error
    with pytest.raises(ValidationError):
        # Missing required fields like 'category', 'sentiment'
        EmailClassification(urgency="high")

def test_email_classification_valid():
    # Valid model
    classification = EmailClassification(
        category="support",
        sentiment="neutral",
        urgency="medium",
        summary="User asking for reset password"
    )
    assert classification.category == "support"
