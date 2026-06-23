from django.urls import path
from . import admin_views as v

app_name = "panel"

urlpatterns = [
    path("", v.dashboard, name="dashboard"),

    # Posts
    path("posts/", v.post_list, name="posts"),
    path("posts/new/", v.post_create, name="post_create"),
    path("posts/<int:pk>/edit/", v.post_edit, name="post_edit"),
    path("posts/<int:pk>/delete/", v.post_delete, name="post_delete"),

    # Categories
    path("categories/", v.category_list, name="categories"),
    path("categories/new/", v.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", v.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", v.category_delete, name="category_delete"),

    # Tags
    path("tags/", v.tag_list, name="tags"),
    path("tags/new/", v.tag_create, name="tag_create"),
    path("tags/<int:pk>/edit/", v.tag_edit, name="tag_edit"),
    path("tags/<int:pk>/delete/", v.tag_delete, name="tag_delete"),

    # Comments
    path("comments/", v.comment_list, name="comments"),
    path("comments/<int:pk>/approve/", v.comment_approve, name="comment_approve"),
    path("comments/<int:pk>/delete/", v.comment_delete, name="comment_delete"),

    # Users
    path("users/", v.user_list, name="users"),
    path("users/<int:pk>/edit/", v.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", v.user_delete, name="user_delete"),

    # Messages
    path("messages/", v.message_list, name="messages"),
    path("messages/<int:pk>/", v.message_detail, name="message_detail"),
    path("messages/<int:pk>/delete/", v.message_delete, name="message_delete"),

    # Settings
    path("settings/", v.settings_view, name="settings"),
]
