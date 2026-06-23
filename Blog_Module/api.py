"""
ArioSport API endpoints for n8n automation.
Proxied through Cloudflare Worker.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from .models import Post, Tag
from Category_Module.models import Category


def check_auth(request):
    """Check Basic Auth credentials. Returns user or None."""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Basic "):
        return None

    import base64
    try:
        decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return None

    user = authenticate(username=username, password=password)
    if user and user.is_staff:
        return user
    return None


@csrf_exempt
@require_http_methods(["POST"])
def create_post_api(request):
    """Create a new blog post. Accepts multipart/form-data."""
    user = check_auth(request)
    if not user:
        return JsonResponse({"error": "Unauthorized. Valid admin credentials required."}, status=401)

    title = request.POST.get("title")
    category_id = request.POST.get("category_id")
    content = request.POST.get("content")

    if not all([title, category_id, content]):
        return JsonResponse(
            {"error": "title, category_id, and content are required."},
            status=400,
        )

    try:
        category = Category.objects.get(id=int(category_id))
    except (Category.DoesNotExist, ValueError):
        return JsonResponse(
            {"error": f"Category with id={category_id} not found."},
            status=404,
        )

    post = Post(
        title=title,
        category=category,
        content=content,
        excerpt=request.POST.get("excerpt", ""),
        status=request.POST.get("status", "draft"),
        is_featured=request.POST.get("is_featured", "false").lower() == "true",
        author=user,
    )

    if "cover_image" in request.FILES:
        post.cover_image = request.FILES["cover_image"]

    post.save()

    tag_names = request.POST.get("tags", "")
    if tag_names:
        for name in tag_names.split(","):
            name = name.strip()
            if name:
                tag, _ = Tag.objects.get_or_create(name=name)
                post.tags.add(tag)

    return JsonResponse(
        {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "status": post.status,
            "url": post.get_absolute_url(),
            "message": "Post created successfully.",
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["GET"])
def list_categories_api(request):
    """List all active categories with their IDs."""
    user = check_auth(request)
    if not user:
        return JsonResponse({"error": "Unauthorized."}, status=401)

    cats = list(Category.objects.filter(is_active=True).values("id", "name", "slug"))
    return JsonResponse({"categories": cats}, safe=False)


@csrf_exempt
@require_http_methods(["GET"])
def api_health(request):
    """Health check endpoint — no auth required."""
    return JsonResponse({"status": "ok", "service": "ArioSport API"})
