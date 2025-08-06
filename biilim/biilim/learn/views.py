import logging
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages

from biilim.core.views import HtmxHttpRequest
from biilim.learn.models import Topic
from biilim.learn.models import Section, Quiz, Question, Choice
from biilim.learn.models import StudentAnswer
from biilim.learn.models import ChatMessage
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
    Render the detail page for a specific topic, including all quiz data.
    """
    # Fetch topic and all related quiz data in a single, efficient query
    topic = get_object_or_404(
        Topic.objects.prefetch_related(
            'sections__quizzes__questions__choices',  # Quizzes for each section
            'quizzes__questions__choices'             # Quizzes for the entire topic
        ), 
        pk=pk
    )
    # Get the main topic quiz (where section is null and it's not graded)
    # This assumes your main topic quiz is graded and not linked to a section
    main_topic_quiz = topic.quizzes.filter(section__isnull=True, is_graded=True).first()

    ctx = {
        "title": topic.title,
        "topic": topic,
        "sections": topic.sections.all(),
        "main_topic_quiz": main_topic_quiz,

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
        if topics.exists():
            ctx["topics"] = topics
        else:
            try:
                # Call AI to generate topic
                json_data = gemini_generate_topic(
                    user_profile=user.profile,
                    prompt=query,
                    response_schema=TopicSchema,
                )
                
                with transaction.atomic():
                    if isinstance(json_data, dict):
                        generated_topic = TopicSchema.model_validate(json_data)
                    else:
                        generated_topic = TopicSchema.model_validate_json(json_data)
                    
                    # 1. Convert supplementary prompts to a format suitable for the database
                    supplementary_prompts_for_db = [p.model_dump() for p in generated_topic.supplementary_prompts]
                    
                    # 2. Create the Topic object
                    new_topic = Topic.objects.create(
                        title=generated_topic.title,
                        description=generated_topic.description,
                        duration=generated_topic.duration,
                        is_recommended=generated_topic.is_recommended,
                        supplementary_prompts=supplementary_prompts_for_db,
                        created_by=user,
                    )
                    
                    # 3. Create Quizzes for each section and the main topic
                    
                    # Create Quiz object for the main topic
                    topic_quiz = Quiz.objects.create(
                        topic=new_topic,
                        is_graded=True,
                    )
                    # Create questions and choices for the main topic quiz
                    for question_data in generated_topic.quiz.questions:
                        new_question = Question.objects.create(
                            quiz=topic_quiz,
                            question_text=question_data.question_text,
                            correct_answer_letter=question_data.correct_answer_letter,
                        )
                        for choice_data in question_data.choices:
                            Choice.objects.create(
                                question=new_question,
                                letter=choice_data.letter,
                                text=choice_data.text,
                            )
                    
                    # 4. Create Sections and their quizzes
                    for section_data in generated_topic.sections:
                        new_section = Section.objects.create(
                            topic=new_topic,
                            title=section_data.title,
                            content=section_data.content,
                            index=section_data.index,
                        )
                        
                        # Create Quiz object for the current section
                        section_quiz = Quiz.objects.create(
                            section=new_section,
                            is_graded=False,
                        )
                        # Create questions and choices for the section quiz
                        for question_data in section_data.quiz.questions:
                            new_question = Question.objects.create(
                                quiz=section_quiz,
                                question_text=question_data.question_text,
                                correct_answer_letter=question_data.correct_answer_letter,
                            )
                            for choice_data in question_data.choices:
                                Choice.objects.create(
                                    question=new_question,
                                    letter=choice_data.letter,
                                    text=choice_data.text,
                                )

                    ctx["topic"] = new_topic
                    messages.success(request, f"Topic '{new_topic.title}' and its quizzes were successfully generated!")
                    return redirect("learn:topic_detail", pk=new_topic.pk)
            
            except Exception as e:
                msg = f"Error saving generated topic and quizzes: {str(e)}"
                logger.error(msg)
                messages.error(request, msg)

            return render(request, "learn/topic_search.html", ctx)
        
    return render(request, "learn/topic_search.html", ctx)

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

from django.http import HttpResponse

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
    user = request.user
    profile = user.profile
    topic = Topic.objects.get(pk=pk)
    if not user_message:
        # If user sends an empty message, return an empty response (HTMX will do nothing)
        return HttpResponse("") 
    # 1. Save User's Message to the database
    ChatMessage.objects.create(
        user=user,
        topic=topic,
        sender="user",
        message_text=user_message,
        chat_type=chat_type
    )
    ai_response = ""
    if chat_type == "explanation":
        # Assumed this function returns a string with the AI's feedback
        ai_response = evaluate_student_explanation(user_message, topic=topic, profile=profile)
    else:
        # Assumed this function returns a string with the AI's chat response
        ai_response = chat_with_student(user_message, topic=topic, profile=profile)

    # 2. Save the AI's Response to the database
    ChatMessage.objects.create(
        user=user,
        topic=topic,
        sender="ai",
        message_text=ai_response,
        chat_type="evaluation_feedback" if chat_type == "explanation" else "general_chat"
    )

    # 3. Render ONLY the new user message and AI response using your partial
    ctx = {
        "user_message": user_message, # Pass the actual message text
        "ai_response": ai_response,
        "chat_type": chat_type, # This might be useful for conditional styling in the partial
    }
    
    # Render the partial template with the chat messages
    return render(request, "learn/hx_chat_message.html", ctx)


@login_required
def get_chat_history_of_topic(request, pk):
    topic = Topic.objects.get(pk=pk)
    chat_history = ChatMessage.objects.filter(user=request.user, topic=topic).order_by('created_at')
    return render(request, "learn/hx_chat_messages_list.html", {"chat_history": chat_history})


@login_required
def hx_submit_quiz(request: HtmxHttpRequest, pk):
    """
    Handles HTMX request to submit a quiz, saves student answers, and returns feedback.
    This view handles both section quizzes and the main topic quiz.
    
    Args:
        request: The HTMX HTTP request object.
        pk: The primary key of the topic (used for context).
    
    Returns:
        HttpResponse: Rendered HTMX partial with quiz feedback.
    """
    if request.method != "POST":
        return HttpResponse(status=405) # Method Not Allowed

    user = request.user
    topic = get_object_or_404(Topic, pk=pk)

    try:
        quiz_id = request.POST.get("quiz_id")
        quiz = get_object_or_404(Quiz, pk=quiz_id)

        correct_answers_count = 0
        total_questions_count = quiz.questions.count()
        
        # Use a transaction to ensure all answers are saved or none are
        with transaction.atomic():
            for question in quiz.questions.all():
                # The name of the input is 'question-{{ question.pk }}'
                student_answer_letter = request.POST.get(f"question-{question.pk}")
                
                if student_answer_letter:
                    is_correct = (student_answer_letter == question.correct_answer_letter)
                    
                    if is_correct:
                        correct_answers_count += 1
                        
                    # Save the student's answer to the database
                    StudentAnswer.objects.create(
                        user=user,
                        question=question,
                        selected_choice_letter=student_answer_letter,
                        is_correct=is_correct
                    )
        
        # Calculate the score
        score_percentage = (correct_answers_count / total_questions_count) * 100 if total_questions_count > 0 else 0
        
        # Prepare context for the feedback partial
        ctx = {
            "is_graded": quiz.is_graded,
            "score_percentage": int(score_percentage),
            "correct_answers": correct_answers_count,
            "total_questions": total_questions_count,
            "quiz_id": quiz_id,
        }
        
        # Return the rendered feedback partial
        return render(request, "learn/hx_quiz_feedback.html", ctx)

    except Exception as e:
        # Log the error for debugging
        # logger.error(f"Error submitting quiz for topic {pk}: {e}")
        return HttpResponse(f"An error occurred: {str(e)}", status=500)


