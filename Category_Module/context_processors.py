def nav_categories(request):
    """Expose active categories to every template (navbar, footer, sidebar)."""
    from .models import Category
    from django.db import OperationalError, ProgrammingError
    try:
        cats = list(Category.objects.filter(is_active=True)[:8])
    except (OperationalError, ProgrammingError):
        cats = []
    return {"nav_categories": cats}
