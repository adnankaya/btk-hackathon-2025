import logging
import os
import json
import re
from django.conf import settings
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from smolagents import CodeAgent, LiteLLMModel

logger = logging.getLogger(__name__)

# --- Configuration ---
# Ensure GEMINI_API_KEY is set in your Django settings
os.environ.setdefault("GEMINI_API_KEY", settings.GEMINI_API_KEY)
CHAT_MODEL_FOR_AGENTS = "gemini/gemini-2.0-flash" # Or gemini-1.5-pro for more complex code generation

# --- New Pydantic Schema for Combined HTML Output ---
class AnimationSchema(BaseModel):
    """Represents a single-page HTML animation with embedded CSS and JavaScript."""
    full_html_code: str
    description: str = "An animated visualization for the student."

# --- The Agent Itself ---
llm_model = LiteLLMModel(
    model_id=CHAT_MODEL_FOR_AGENTS,
    api_key=settings.GEMINI_API_KEY,
    num_ctx=8192, # Context window size
)

# The agent now has no tools, as it's a direct code generation task
visual_agent = CodeAgent(
    name="HTMLAnimationGenerator",
    tools=[], # No tools needed for this direct generation task
    model=llm_model,
    max_steps=1, # Allow for multiple steps of reasoning if needed
)

# --- Public function to invoke the agent ---
def get_html_animation_for_topic(topic_title: str, topic_description: str, user_profile: dict, section_title: Optional[str] = None) -> AnimationSchema:
    """
    Invokes the smolagents agent to generate a single HTML string containing
    HTML, CSS, and JavaScript for an educational animation.
    
    Args:
        topic_title (str): The title of the current topic.
        topic_description (str): The description of the current topic.
        user_profile (dict): The student's profile data.
        section_title (Optional[str]): The title of the specific section, if applicable.
        
    Returns:
        AnimationSchema: A Pydantic object containing the generated full HTML code and a description.
    """
    topic_context = f"Topic: {topic_title}\nDescription: {topic_description}"
    if section_title:
        topic_context += f"\nSection: {section_title}"
    
    user_profile_str = "\n".join([f"- {k}: {v}" for k, v in user_profile.items()])

    # --- UPDATED PROMPT INSTRUCTION ---
    # This prompt now explicitly guides the CodeAgent to generate the combined HTML string.
    prompt_instruction = f"""
    You are an expert web developer specializing in creating concise, single-page educational animations using HTML, CSS, and JavaScript. Your task is to generate the complete HTML code for an animation that visually explains a learning concept for a student.

    ### Student Profile
    {user_profile_str}

    ### Learning Context
    {topic_context}

    ### Instructions
    1.  **Analyze the concept:** Understand the core concept from the "Learning Context".
    2.  **Design a simple animation:** Create a visual representation of the concept. The animation should be clear, concise, and directly illustrate the key idea.
    3.  **Personalize (Optional but encouraged):** If possible, subtly incorporate elements or themes related to the student's hobbies, city, or cultural background into the animation's design or narrative (e.g., colors, shapes, analogies).
    4.  **Generate Combined HTML:** Produce a single HTML string that includes:
        * A `<style>` block for all CSS.
        * A `<div>` (or other appropriate HTML tags) for the animated elements.
        * A `<script>` block for all JavaScript.
        * **Important:** The generated code should NOT include `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`, or `<title>` tags. It should only contain the content that would typically go *inside* the `<body>` tag, specifically the `<style>`, `<div>`, and `<script>` elements.
        * Ensure the JavaScript is self-executing or uses `DOMContentLoaded` to run.
        * The animation should be smooth and visually appealing.
    5.  **Provide a description:** Write a brief, clear description of what the animation visualizes and how it helps understand the concept.
    6.  **Return JSON:** Your final output MUST be a JSON object, formatted strictly according to the `AnimationSchema` Pydantic schema provided below. Do not include any extra text or markdown outside this JSON.

    AnimationSchema schema:
    {AnimationSchema.model_json_schema()}
    """
    
    logger.info("Invoking smolagents agent for HTML animation...")
    try:
        # Run the agent with the detailed prompt
        response_text = visual_agent.run(prompt_instruction)
        
        # The agent returns the final answer as a string, which we need to parse.
        # It's possible the agent might wrap the JSON in markdown code blocks, so we need to extract it.
        json_match = re.search(r"```json\n(.*)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text # Assume it's plain JSON if no markdown block

        parsed_response = AnimationSchema.model_validate_json(json_str)
        return parsed_response
    except ValidationError as e:
        logger.error(f"Failed to validate AI response for HTML animation: {e.errors()}")
        # Return a fallback object with a simple error message
        return AnimationSchema(full_html_code="<p>Failed to generate a valid animation code. Please try again.</p>", description="Error generating animation.")
    except Exception as e:
        logger.error(f"Error invoking smolagents agent for HTML animation: {e}")
        # Return a fallback object with a simple error message
        return AnimationSchema(full_html_code="<p>An unexpected error occurred while generating the animation.</p>", description="Error generating animation.")
