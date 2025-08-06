import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from biilim.core.views import HtmxHttpRequest
from biilim.learn.models import Topic
from biilim.learn.schemas import TopicSchema
from biilim.ai.api_client import gemini_generate_topic
from biilim.ai.api_client import evaluate_student_explanation, chat_with_student

logger = logging.getLogger(__name__)

def index(request):
    """
    Render the index page for the learn app.
    
    Args:
        request: The HTTP request object.
    
    Returns:
        HttpResponse: Rendered index page.
    """
    ctx = {
        "title": "Learn",
        "description": "Explore topics, browse content, and enhance your knowledge.",
    }
    return render(request, "learn/index.html", ctx)

@login_required
def topic_detail(request, pk):
    """
    Render the detail page for a specific topic.
    
    Args:
        request: The HTTP request object.
        pk: The primary key of the topic to display.
    
    Returns:
        HttpResponse: Rendered topic detail page.
    """
    topic = Topic.objects.get(pk=pk)
    ctx = {
        "title": topic.title,
        "topic": topic,
        "sections": topic.sections.all(),
    }
    return render(request, "learn/topic_detail.html", ctx)

def topics(request):
    ctx = {
        "title": "All Topics",
        "topics": Topic.objects.all().order_by("-created_at"),
    }

    return render(request, "learn/topics.html", ctx)


@login_required
def upload(request):
    # handle file upload logic here
    """
    Render the upload page for the learn app.

    Args:
        request: The HTTP request object.

    Returns:

        HttpResponse: Rendered upload page.
    """
    return render(request, "learn/upload.html", {"title": "Upload Content"})

@login_required
def topic_search(request):
    """
    Render the topic selection page for the learn app.
    
    Args:
        request: The HTTP request object.
    
    Returns:
        HttpResponse: Rendered topic selection page.
    """
    user = request.user
    query = request.GET.get("query")
    if query:
        ctx = {
            "title": "Search Results",
            "query": query,
        }
        topics = Topic.objects.filter(title__icontains=query).order_by("-created_at") # NOTE we may increase search functionality later
        if topics:
            ctx["topics"] = topics
        else:
            # import ipdb; ipdb.set_trace()
            json_data = gemini_generate_topic(
                user_profile=user.profile,
                prompt=query,
                response_schema=TopicSchema,
            )
            try:
                with transaction.atomic():
                    if isinstance(json_data, dict):
                        generated_topic = TopicSchema.model_validate(json_data)
                    else:
                        generated_topic = TopicSchema.model_validate_json(json_data)
                    # Convert supplementary prompts to a format suitable for the database
                    supplementary_prompts_for_db = [p.model_dump() for p in generated_topic.supplementary_prompts]
                    # save the generated topic to the database
                    new_topic = Topic.objects.create(
                        title=generated_topic.title,
                        description=generated_topic.description,
                        duration=generated_topic.duration,
                        is_recommended=generated_topic.is_recommended,
                        supplementary_prompts=supplementary_prompts_for_db,
                    )
                    for section in generated_topic.sections:
                        new_topic.sections.create(
                            title=section.title,
                            content=section.content,
                            index=section.index,
                        )
                    ctx["generated_topic"] = new_topic
            except Exception as e:
                msg = f"Error saving generated topic: {str(e)}"
                logger.error(msg)
                messages.error(request, msg)

        return render(request, "learn/topic_search.html", ctx)
        
    return render(request, "learn/topic_search.html", {"title": "Select a Topic"})

def hx_recommended_topics(request: HtmxHttpRequest):
    """
    Handle HTMX request to fetch recommended topics.
    
    Args:
        request: The HTMX HTTP request object.
    
    Returns:
        HttpResponse: Rendered HTMX response with recommended topics.
    """
    recommended_topics = Topic.objects.filter(is_recommended=True).order_by("-created_at")[:6]
    return render(request, "learn/hx_recommended_topics.html", {"recommended_topics": recommended_topics})


@login_required
def hx_chat_about_topic(request:HtmxHttpRequest, pk):
    """
    Handle HTMX request to chat about a specific topic.
    Args:
        request: The HTMX HTTP request object.
        pk: The primary key of the topic to chat about.
    Returns:
        HttpResponse: Rendered HTMX response for the chat interface.
    
    """
    chat_type = request.POST.get("chat_type")
    user_message = request.POST.get("user_message")
    profile = request.user.profile
    topic = Topic.objects.get(pk=pk)
    ai_response = ""
    if chat_type == "explanation":
        # Assumed this function returns a string with the AI's feedback
        ai_response = evaluate_student_explanation(user_message, topic=topic, profile=profile)
    else:
        # Assumed this function returns a string with the AI's chat response
        ai_response = chat_with_student(user_message, topic=topic, profile=profile)

    ctx = {
        "user_message": user_message,
        "ai_response": ai_response,
        "chat_type": chat_type,
    }
    
    # Render the partial template with the chat messages
    return render(request, "learn/hx_chat_message.html", ctx)
