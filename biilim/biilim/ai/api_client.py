import logging
from django.conf import settings
from pydantic import BaseModel as PydanticBaseModel
import json

from google import genai
from biilim.users.models import Profile
from biilim.learn.models import Topic

logger = logging.getLogger(__name__)


def get_local_development_api_response(file_name="gemini_topic"):
    with open(f"{settings.APPS_DIR}/ai/example_responses/{file_name}.json", "r") as file:
        
        return json.load(file)

def get_topic_prompt(user_profile: Profile, topic_query: str) -> str:
    """
    Generate a highly structured prompt for the Gemini API to create a topic.
    
    The prompt incorporates student profile data to personalize the learning path.
    
    Args:
        user_profile (Profile): The student's profile data.
        topic_query (str): The user-provided prompt for the topic.
    
    Returns:
        str: The formatted prompt for the Gemini API.
    """
    
    # Construct the personalized prompt string
    prompt = f"""
    You are an expert AI study buddy. Your task is to generate a comprehensive and personalized learning topic for a student.

    ### Student Profile
    The following information should be used to tailor the content and examples.
    - **Age:** {user_profile.age}
    - **City:** {user_profile.city}
    - **Country:** {user_profile.country}
    - **Cultural Background:** {user_profile.cultural_background}
    - **Hobbies:** {user_profile.hobbies}
    - **Preferred Learning Styles:** {user_profile.learning_styles}

    ### Student's Learning Topic Request
    - **Topic Query:** {topic_query}

    ### Instructions for Content Generation

    1.  **Primary Content:** Generate the full learning topic in a detailed, informative `reading_writing` style. This content should be logical, easy to follow, and broken down into clear sections.
    2.  **Personalization:** Weave in relevant examples related to the student's hobbies, location, or cultural background to make the content more relatable.
    3.  **Supplementary Prompts:** For each of the student's learning styles (excluding 'reading_writing'), generate a separate, highly specific instruction. These prompts will be used by your functions to create supplementary learning materials.
        - If the style is **'visual'**: Create a prompt that describes a clear and relevant image, diagram, or flowchart that would help the student visualize the core concept.
        - If the style is **'kinesthetic'**: Create a prompt that describes a hands-on exercise or activity the student can do to physically practice the concept.
        - If the style is **'real_world'**: Create a prompt that suggests a simple activity using everyday objects or observations from the real world.
        - If the style is **'simulation'**: Create a prompt that describes the core mechanics of a simple interactive simulation (e.g., a process with a draggable element, a step-by-step animation).

    ### Output Structure
    Provide the response as a single JSON object with the following fields:
    - `title`: The title of the topic.
    - `description`: A detailed overview of the topic.
    - `duration`: An estimated duration in minutes to complete the topic.
    - `sections`: An array of objects, where each object has a `title` and `content` for a specific section.
    - `supplementary_prompts`: An array of objects, where each object has a `style` and a `prompt` string for generating additional content. This array should only contain prompts for the styles listed in the student's profile.
    """
    
    return prompt

def gemini_generate_topic(user_profile: Profile, prompt: str, response_schema: PydanticBaseModel, model: str = "gemini-2.0-flash"):
    """
    Generates a topic using the Gemini API based on a structured prompt.
    """
    # if settings.DEBUG:
    #     logger.info("Using local development API response for gemini_generate_topic")
    #     return get_local_development_api_response("topic")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Use the new structured prompt function
    structured_prompt = get_topic_prompt(user_profile, prompt)
    
    response = client.models.generate_content(
        model=model,
        contents=structured_prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )
    return response.text


def evaluate_student_explanation(user_message: str, topic: Topic, profile: Profile) -> str:
    """
    Evaluates a student's explanation of a topic and provides feedback.
    
    Args:
        user_message (str): The student's explanation message.
        topic (Topic): The topic being discussed.
        profile (Profile): The student's profile data.
    
    Returns:
        str: The AI's feedback on the student's explanation.
    """
    # Placeholder for actual evaluation logic
    # This should call the Gemini API or any other service to evaluate the explanation
    return f"Feedback on your explanation about {topic.title}: {user_message}"

def chat_with_student(user_message: str, topic: Topic, profile: Profile) -> str:
    """
    Handles a chat interaction with a student about a specific topic.
    
    Args:
        user_message (str): The student's message.
        topic (Topic): The topic being discussed.
        profile (Profile): The student's profile data.
    
    Returns:
        str: The AI's response to the student's message.
    """
    # Placeholder for actual chat logic
    # This should call the Gemini API or any other service to generate a response
    return f"AI response to your message about {topic.title}: {user_message}"
