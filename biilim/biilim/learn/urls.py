from django.urls import path


from . import views

app_name = "learn"

urlpatterns = [
    path("", view=views.index, name="index"),
    path("<int:pk>/", view=views.topic_detail, name="topic_detail"),
    path("topics/", view=views.topics, name="topics"),
    path("upload/", view=views.upload, name="upload"),
    path("topic-search/", view=views.topic_search, name="topic_search"),
    
]
