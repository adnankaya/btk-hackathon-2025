from django.db import models

from biilim.core.models import BaseModel


class Topic(BaseModel):
    """
    Model representing a topic in the learn app.
    This can be used to categorize and manage learning content.
    """

    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(default=0, help_text="Duration in minutes")
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="created_topics",
        null=True,
        blank=True,
    )
    is_recommended = models.BooleanField(default=False, help_text="Whether this topic is recommended for users")
    supplementary_prompts = models.JSONField(default=list, blank=True, null=True)
    

    def __str__(self) -> str:
        return self.title

class Section(models.Model):
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    index = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ["index"]

    def __str__(self):
        return f"{self.topic.title} - {self.title}"



class ChatMessage(BaseModel):
    """
    Model representing a single message in the chat history between a user and the AI.
    """
    SENDER_CHOICES = [
        ("user", "User"),
        ("ai", "AI"),
    ]
    CHAT_TYPE_CHOICES = [
        ("general_chat", "General Chat"),
        ("explanation_submission", "Explanation Submission"),
        ("evaluation_feedback", "Evaluation Feedback"),
        ("welcome_message", "Welcome Message"), # For initial AI messages
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="chat_messages")
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE, related_name="chat_messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message_text = models.TextField()
    chat_type = models.CharField(
        max_length=50,
        choices=CHAT_TYPE_CHOICES,
        default="general_chat",
        help_text="Type of chat message for context/logging"
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self) -> str:
        return f"{self.sender.upper()} on {self.topic.title} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

