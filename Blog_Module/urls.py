from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.blog_list, name="list"),
    path("search/", views.search, name="search"),
    path("tag/<str:slug>/", views.tag_posts, name="tag"),
    path("<str:slug>/", views.post_detail, name="post_detail"),
]
