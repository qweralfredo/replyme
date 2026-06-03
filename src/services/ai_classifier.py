import os
import structlog
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
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
        self.api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required.")
            
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"
        self.cached_content_name = self._init_cache()

    def _init_cache(self) -> str:
        kb_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.txt')
        if not os.path.exists(kb_path):
            logger.warning("knowledge_base.txt not found. Caching will fail if not provided.")
            return None
            
        logger.info("Uploading knowledge base to Gemini API for context caching...")
        
        # Upload the file to Gemini API
        uploaded_file = self.client.files.upload(file=kb_path)
        logger.info("File uploaded", file_uri=uploaded_file.uri, name=uploaded_file.name)
        
        # Check for existing caches
        existing_caches = list(self.client.caches.list())
        for cache in existing_caches:
            if getattr(cache, 'model', '') == f'models/{self.model_name}':
                logger.info("Found existing cache", cache_name=cache.name)
                # For simplicity, we could reuse it. But since we just uploaded a new file,
                # let's create a new one to be safe, or just use the first existing one.
                # Actually, deleting old caches prevents billing leaks.
                try:
                    self.client.caches.delete(name=cache.name)
                    logger.info("Deleted old cache", cache_name=cache.name)
                except Exception as e:
                    logger.warning("Could not delete old cache", error=str(e))
        
        logger.info("Creating new CachedContent...")
        cached_content = self.client.caches.create(
            model=self.model_name,
            config=types.CreateCachedContentConfig(
                contents=[uploaded_file],
                system_instruction="You are an expert email classifier. Use the provided knowledge base to strictly follow operational procedures when classifying and replying to emails.",
                ttl="3600s" # Cache for 1 hour to avoid excessive billing
            )
        )
        logger.info("Cache created successfully", cache_name=cached_content.name)
        return cached_content.name

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def classify_email(self, email_body: str) -> EmailClassification:
        logger.info("Classifying email content", body_length=len(email_body))

        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EmailClassification,
                temperature=0.2,
            )
            
            # Inject cache if available
            if self.cached_content_name:
                config.cached_content = self.cached_content_name
            else:
                config.system_instruction = "You are an expert email classifier."

            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Classify the following email:\n\n{email_body}",
                config=config,
            )
            
            # Parse the JSON response manually since we are using native google-genai
            import json
            data = json.loads(resp.text)
            classification = EmailClassification(**data)
            
            logger.info("Classification successful", category=classification.category, urgency=classification.urgency)
            return classification
        except Exception as e:
            logger.error("Failed to classify email", error=str(e))
            raise
