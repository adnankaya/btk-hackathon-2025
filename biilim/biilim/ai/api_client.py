import logging
from django.conf import settings
from pydantic import BaseModel as PydanticBaseModel
import json

from google import genai
from biilim.users.models import Profile
from biilim.learn.models import Topic
from biilim.learn.models import ChatMessage

logger = logging.getLogger(__name__)


def get_local_development_api_response(file_name="gemini_topic"):
    with open(f"{settings.APPS_DIR}/ai/example_responses/{file_name}.json", "r") as file:
        
        return json.load(file)

def get_topic_prompt(user_profile: Profile, topic_query: str) -> str:
    """
    Generate a highly structured prompt for the Gemini API to create a topic.
    
    This version includes instructions for generating quizzes at the topic and section level.
    
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

    4.  **Quiz Generation:**
        - **Section Quizzes:** For **EACH** section you generate, create a short, non-graded multiple-choice quiz with 1 to 3 questions that test the content of that specific section.
        - **Topic Quiz:** In addition to the section quizzes, generate a single, comprehensive, graded multiple-choice quiz for the entire topic. This quiz should have 3 to 5 questions covering the main points of all sections.
        - **Quiz Format:** Ensure each question has a `question_text`, four choices labeled "A", "B", "C", and "D", and a `correct_answer_letter` that is one of "A", "B", "C", or "D".

    ### Output Structure
    Provide the response as a single JSON object with the following fields:
    - `title`: The title of the topic.
    - `description`: A detailed overview of the topic.
    - `duration`: An estimated duration in minutes to complete the topic.
    - `sections`: An array of objects, where each object has a `title`, `content` for a specific section, and a `quiz` field containing a `QuizSchema` object for that section.
    - `supplementary_prompts`: An array of objects, where each object has a `style` and a `prompt` string for generating additional content. This array should only contain prompts for the styles listed in the student's profile.
    - `quiz`: A `QuizSchema` object containing the questions for the entire topic.
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


def get_explanation_evaluation_prompt(user_explanation: str, topic_data: dict, profile_data: dict) -> str:
    """
    Generates a structured prompt for the Gemini API to evaluate a student's explanation.
    
    Args:
        user_explanation (str): The student's explanation.
        topic_data (dict): A dictionary containing the topic's title, description, and sections.
        profile_data (dict): A dictionary containing the student's profile information.
        
    Returns:
        str: The formatted prompt for the Gemini API.
    """
    
    topic_sections_content = "\n".join([
        f"Section: {s['title']}\nContent: {s['content']}" 
        for s in topic_data.get('sections', [])
    ])

    prompt = f"""
    You are an expert AI tutor specializing in evaluating student understanding. Your goal is to provide constructive, personalized feedback on a student's explanation of a topic.

    ### Student Profile
    Use this information to tailor your feedback, examples, and suggestions for remediation.
    - **Age:** {profile_data.get('age', 'N/A')}
    - **City:** {profile_data.get('city', 'N/A')}
    - **Country:** {profile_data.get('country', 'N/A')}
    - **Cultural Background:** {profile_data.get('cultural_background', 'N/A')}
    - **Hobbies:** {profile_data.get('hobbies', 'N/A')}
    - **Preferred Learning Styles:** {profile_data.get('learning_styles', 'N/A')}

    ### Original Topic Content
    This is the content the student was expected to learn. Refer to this for accuracy and completeness.
    - **Topic Title:** {topic_data.get('title', 'N/A')}
    - **Topic Description:** {topic_data.get('description', 'N/A')}
    - **Topic Sections:**
    {topic_sections_content}

    ### Student's Explanation
    This is the explanation provided by the student that you need to evaluate.
    "{user_explanation}"

    ### Evaluation Instructions

    1.  **Acknowledge and Motivate:** Start with positive reinforcement, acknowledging their effort.
    2.  **Identify Strengths:** Clearly state what the student explained well or understood correctly. Be specific.
    3.  **Identify Gaps/Misconceptions:** Point out areas where their understanding is incomplete, inaccurate, or missing key details. Frame this constructively.
    4.  **Suggest Next Steps:** Provide actionable advice for improvement. This could include:
        * Revisiting a specific section of the topic.
        * Suggesting a different learning style for a particular concept (e.g., "Perhaps a visual diagram would help with X?").
        * Proposing a real-world example or a simple practice exercise.
        * Asking a clarifying question to prompt deeper thought.
    5.  **Tone:** Maintain a supportive, encouraging, and clear tone.
    6.  **Conciseness:** Keep the feedback concise but comprehensive. Aim for a paragraph or two.

    Your response should be the feedback directly, without any conversational filler or markdown formatting beyond what's necessary for readability (e.g., bolding key terms).
    """
    return prompt


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
    # Prepare topic data for the prompt
    topic_sections_list = [
        {"title": section.title, "content": section.content}
        for section in topic.sections.all()
    ]
    topic_data = {
        "title": topic.title,
        "description": topic.description,
        "sections": topic_sections_list,
    }

    # Prepare profile data for the prompt
    profile_data = {
        "age": profile.age,
        "city": profile.city,
        "country": profile.country,
        "cultural_background": profile.cultural_background,
        "hobbies": profile.hobbies,
        "learning_styles": profile.learning_styles,
    }

    # Construct the structured prompt
    structured_prompt = get_explanation_evaluation_prompt(user_message, topic_data, profile_data)

    # Initialize Gemini client (ensure settings.GEMINI_API_KEY is configured)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Or gemini-1.5-pro for more complex reasoning
            contents=structured_prompt,
            # No response_schema here as we want a plain string feedback
        )
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API for explanation evaluation: {e}")
        return "I'm sorry, I couldn't evaluate your explanation right now. Please try again later!"


def get_chat_prompt(user_message: str, topic_data: dict, profile_data: dict, chat_history: list[dict]) -> str:
    """
    Generates a structured prompt for the Gemini API to handle general chat.
    
    This version includes chat history to maintain conversational context.
    
    Args:
        user_message (str): The student's current message.
        topic_data (dict): A dictionary containing the topic's title and description.
        profile_data (dict): A dictionary containing the student's profile information.
        chat_history (list[dict]): A list of past chat messages.
        
    Returns:
        str: The formatted prompt for the Gemini API.
    """
    
    history_str = ""
    if chat_history:
        history_str = "\n".join([f"{msg['sender'].capitalize()}: {msg['message_text']}" for msg in chat_history])
    else:
        history_str = "No prior chat history for this topic."

    prompt = f"""
    You are an expert AI study buddy. Your goal is to have a helpful, friendly, and contextual conversation with a student.

    ### Student Profile
    Use this information to tailor your response and make it more personalized.
    - **Age:** {profile_data.get('age', 'N/A')}
    - **City:** {profile_data.get('city', 'N/A')}
    - **Country:** {profile_data.get('country', 'N/A')}
    - **Cultural Background:** {profile_data.get('cultural_background', 'N/A')}
    - **Hobbies:** {profile_data.get('hobbies', 'N/A')}
    - **Preferred Learning Styles:** {profile_data.get('learning_styles', 'N/A')}

    ### Current Topic Context
    The current topic the student is studying is about **{topic_data.get('title', 'N/A')}**.
    Here is a brief description to give you context: {topic_data.get('description', 'N/A')}

    ### Chat History
    This is a transcript of the conversation so far.
    {history_str}

    ### Student's Current Message
    "{user_message}"

    ### Conversational Instructions

    1.  **Respond Directly:** Answer the student's message clearly and concisely.
    2.  **Maintain Context:** Refer to the chat history and the current topic to ensure your response is relevant and avoids repeating information.
    3.  **Provide Relatable Examples:** Use the student's profile data (hobbies, location, etc.) to offer personalized and easy-to-understand examples.
    4.  **Tone:** Be friendly, supportive, and encouraging. Use a positive and conversational tone, like a helpful tutor.
    5.  **Conciseness:** Keep your response brief, but informative. Avoid overly long paragraphs.

    Your response should be the message you would say to the student directly, without any conversational filler or markdown formatting beyond what's necessary for readability.
    """
    return prompt


def chat_with_student(user_message: str, topic: Topic, profile: Profile) -> str:
    """
    Handles a chat interaction with a student about a specific topic,
    including the conversation history for context.
    
    Args:
        user_message (str): The student's message.
        topic (Topic): The topic being discussed.
        profile (Profile): The student's profile data.
    
    Returns:
        str: The AI's response to the student's message.
    """
    # Prepare topic data for the prompt
    topic_data = {
        "title": topic.title,
        "description": topic.description,
    }

    # Prepare profile data for the prompt
    profile_data = {
        "age": profile.age,
        "city": profile.city,
        "country": profile.country,
        "cultural_background": profile.cultural_background,
        "hobbies": profile.hobbies,
        "learning_styles": profile.learning_styles,
    }

    # Fetch chat history from the database
    # IMPORTANT FIX: Convert the QuerySet to a list before slicing
    chat_history_queryset = ChatMessage.objects.filter(
        user=profile.user,
        topic=topic,
    ).exclude(
        chat_type__in=["explanation_submission", "evaluation_feedback"]
    ).order_by('created_at').values('sender', 'message_text')
    
    # Convert to a list to allow standard Python slicing with negative indices
    chat_history_list = list(chat_history_queryset)
    
    # Exclude the most recent message (which is the user's current message)
    formatted_history = chat_history_list[:-1] 

    # Construct the structured prompt
    structured_prompt = get_chat_prompt(user_message, topic_data, profile_data, formatted_history)

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=structured_prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Error calling Gemini API for general chat with history: {e}")
        return "I'm sorry, I couldn't respond to that right now. Please try again later!"

