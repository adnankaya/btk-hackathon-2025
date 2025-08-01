
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db.models import EmailField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for biilim.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:me")




class Profile(models.Model):
    """
    User profile model.
    This is used to store additional information about the user.
    """

    LEARNING_STYLE_CHOICES = [
        ("visual", "Visual"),
        ("auditory", "Auditory"),
        ("reading_writing", "Reading/Writing"),
        ("kinesthetic", "Kinesthetic/Doing"),
        ("simulation", "Simulation"),
        ("real_world", "Real-world Practice"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.PositiveIntegerField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    cultural_background = models.CharField(max_length=255, blank=True)
    hobbies = models.CharField(max_length=255, blank=True, help_text="Comma-separated")
    learning_styles = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated values from LEARNING_STYLE_CHOICES"
    )

    def __str__(self) -> str:
        return f"{self.user.email} Profile"
