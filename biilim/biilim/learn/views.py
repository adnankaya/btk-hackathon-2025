from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from biilim.core.views import HtmxHttpRequest
from biilim.learn.models import Topic

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


def topic_search(request):
    """
    Render the topic selection page for the learn app.
    
    Args:
        request: The HTTP request object.
    
    Returns:
        HttpResponse: Rendered topic selection page.
    """
    query = request.GET.get("query")
    if query:
        topics = Topic.objects.filter(title__icontains=query).order_by("-created_at")
        ctx = {
            "title": "Search Results",
            "topics": topics,
            "query": query,
        }
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
