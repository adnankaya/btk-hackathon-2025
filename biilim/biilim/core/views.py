from django.shortcuts import render
from django.http import HttpRequest
from django_htmx.middleware import HtmxDetails


# internals

# Typing pattern recommended by django-stubs:
# https://github.com/typeddjango/django-stubs#how-can-i-create-a-httprequest-thats-guaranteed-to-have-an-authenticated-user
class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


def custom_http_404_page(request, exception):
    context = {}
    return render(request, "errors/404.html", context)


def custom_http_500_page(request, template_name="errors/500.html"):
    context = {}
    return render(request, template_name, context)

