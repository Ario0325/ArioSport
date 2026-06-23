from django.contrib import admin
from .models import Post, Tag, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("name", "body", "is_approved", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "is_featured", "views", "published_at")
    list_filter = ("status", "is_featured", "category", "created_at")
    search_fields = ("title", "content", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    list_editable = ("status", "is_featured")
    date_hierarchy = "published_at"
    inlines = [CommentInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("name", "post", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("name", "body")
    list_editable = ("is_approved",)
    actions = ["approve_comments"]

    @admin.action(description="تایید دیدگاه‌های انتخاب‌شده")
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
