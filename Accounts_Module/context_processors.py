def admin_badges(request):
    """Counts for the admin sidebar badges (only computed for staff)."""
    data = {}
    if request.user.is_authenticated and request.user.is_staff:
        from Blog_Module.models import Comment
        from Core_Module.models import ContactMessage
        data["pending_comments_count"] = Comment.objects.filter(is_approved=False).count()
        data["unread_messages_count"] = ContactMessage.objects.filter(is_read=False).count()
    return data
