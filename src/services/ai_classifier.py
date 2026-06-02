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
    response: str = Field(description="A draft of a professional, polite and direct reply to the customer's email based on the context.")

class AIClassifierService:
    def __init__(self):
        # We assume GOOGLE_API_KEY is available in the environment
        self.api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY is not set. Real AI classification will fail.")
            
        self.client = instructor.from_genai(
            genai.Client(api_key=self.api_key),
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def classify_email(self, email_body: str) -> EmailClassification:
        logger.info("Classifying email content", body_length=len(email_body))

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
