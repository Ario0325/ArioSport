from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
]
