import logging
from django.conf import settings
from pydantic import BaseModel as PydanticBaseModel
import json

from google import genai


logger = logging.getLogger(__name__)


def get_local_development_api_response(file_name="gemini_topic"):
    with open(f"{settings.APPS_DIR}/ai/example_responses/{file_name}.json", "r") as file:
        
        return json.load(file)

def get_topic_prompt(prompt: str) -> str:
    """
    Generate a prompt for the Gemini API to create a topic.
    
    Args:
        prompt (str): The user-provided prompt for the topic.
    
    Returns:
        str: The formatted prompt for the Gemini API.
    """
    res = f"""Create a topic based on the following prompt: 
        {prompt}\n\nPlease provide a detailed description, duration(in minutes), and sections for the topic."""
    return res

def gemini_generate_topic(prompt: str, response_schema: PydanticBaseModel,model: str = "gemini-2.0-flash"):
    """
    
    """
    if settings.DEBUG:
        logger.info("Using local development API response for gemini_generate_topic", 
                    extra=dict(detail="Using local development API response")
                    )
        return get_local_development_api_response("gemini_topic")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=model,
        contents=get_topic_prompt(prompt),
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return response.text