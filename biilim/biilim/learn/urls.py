from django.urls import path


from . import views

app_name = "learn"

urlpatterns = [
    # htmx paths
    path("hx/recommended-topics/", view=views.hx_recommended_topics, name="hx-recommended-topics"),
    path("hx/<int:pk>/chat", view=views.hx_chat_about_topic, name="hx-chat"),
    path("hx/<int:pk>/submit-quiz", view=views.hx_submit_quiz, name="hx-submit-quiz"),
    # URL for topic-level visual helpers (no section_pk)
    path(
        "topic/<int:topic_pk>/visual-helpers/",
        views.hx_get_visual_helpers,
        name="hx-get-visual-helpers-topic",
    ),
    
    # URL for section-level visual helpers (with section_pk)
    path(
        "topic/<int:topic_pk>/section/<int:section_pk>/visual-helpers/",
        views.hx_get_visual_helpers,
        name="hx-get-visual-helpers-section",
    ),
    path("hx/<int:pk>/chat-history-of-topic", view=views.get_chat_history_of_topic, name="hx-get-chat-history-of-topic"),


    # paths
    path("<int:pk>/", view=views.topic_detail, name="topic_detail"),
    path("topics/", view=views.topics, name="topics"),
    path("upload/", view=views.upload, name="upload"),
    path("topic-search/", view=views.topic_search, name="topic_search"),
    path("", view=views.index, name="index"),
    
]
