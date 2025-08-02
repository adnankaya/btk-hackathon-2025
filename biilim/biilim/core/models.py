from django.db import models

class BaseModel(models.Model):
    """
    Base model with common fields for all models in the application.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True  # This model will not create a database table
        ordering = ["-created_at"]  # Default ordering by creation date
