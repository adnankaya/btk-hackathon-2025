from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

from biilim.users.models import User, Profile


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:me")


user_redirect_view = UserRedirectView.as_view()


@login_required
def users_me(request):
    user = request.user
    profile, _created = Profile.objects.get_or_create(user=user)
    ctx = {
        "title": _("My Profile Page"),
        "profile": profile,
    }

    if request.method == "POST":
        age = request.POST.get("age")
        city = request.POST.get("city", "")
        country = request.POST.get("country", "")
        cultural_background = request.POST.get("cultural_background", "")
        hobbies = request.POST.get("hobbies","")
        learning_styles = request.POST.get("learning_styles_final") or ""

        # Save to profile
        profile.age = age
        profile.city = city
        profile.country = country
        profile.cultural_background = cultural_background
        profile.hobbies = hobbies
        profile.learning_styles = learning_styles
        profile.save()

        ctx["success"] = True
        messages.success(request, _("Profile updated successfully."))
        return redirect("users:me")

    return render(request, "users/me.html", ctx)

