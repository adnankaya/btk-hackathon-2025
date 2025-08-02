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