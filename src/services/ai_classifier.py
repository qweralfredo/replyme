import os
import structlog
from pydantic import BaseModel, Field
import instructor
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

class EmailClassification(BaseModel):
    category: str = Field(description="The category of the email (e.g., support, sales, spam, general)")
    sentiment: str = Field(description="The sentiment of the email (positive, neutral, negative)")
    urgency: str = Field(description="The urgency of the email (low, medium, high)")
    summary: str = Field(description="A brief executive summary of the email content")

class AIClassifierService:
    def __init__(self):
        # We assume GOOGLE_API_KEY is available in the environment
        self.api_key = os.environ.get("GOOGLE_API_KEY", "dummy_key_for_tests")
        self.client = instructor.from_gemini(
            genai.Client(api_key=self.api_key),
            mode=instructor.Mode.GEMINI_JSON,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def classify_email(self, email_body: str) -> EmailClassification:
        logger.info("Classifying email content", body_length=len(email_body))
        
        # If testing with dummy key, we mock the response to avoid API calls without proper credentials
        if self.api_key == "dummy_key_for_tests":
            logger.info("Using dummy API key, returning mocked classification")
            return EmailClassification(
                category="general",
                sentiment="neutral",
                urgency="low",
                summary="Mocked summary"
            )

        try:
            resp = self.client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "You are an expert email classifier."},
                    {"role": "user", "content": f"Classify the following email:\n\n{email_body}"}
                ],
                response_model=EmailClassification,
            )
            logger.info("Classification successful", category=resp.category, urgency=resp.urgency)
            return resp
        except Exception as e:
            logger.error("Failed to classify email", error=str(e))
            raise
