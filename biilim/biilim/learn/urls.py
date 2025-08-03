from django.urls import path


from . import views

app_name = "learn"

urlpatterns = [
    # htmx paths
    path("hx/recommended-topics/", view=views.hx_recommended_topics, name="hx-recommended-topics"),


    # paths
    path("<int:pk>/", view=views.topic_detail, name="topic_detail"),
    path("topics/", view=views.topics, name="topics"),
    path("upload/", view=views.upload, name="upload"),
    path("topic-search/", view=views.topic_search, name="topic_search"),
    path("", view=views.index, name="index"),
    
]
