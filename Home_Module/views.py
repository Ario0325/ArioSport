from django.shortcuts import render
from django.db.models import Count, Q, Sum
from Blog_Module.models import Post
from Category_Module.models import Category


def index(request):
    published = Post.published.select_related("author", "category")
    featured = published.filter(is_featured=True).first() or published.first()
    side_featured = published.exclude(pk=featured.pk if featured else None)[:2]
    latest = published.exclude(pk=featured.pk if featured else None)[:6]

    categories = (Category.objects.filter(is_active=True)
                  .annotate(n=Count("posts", filter=Q(posts__status="published")))[:6])

    stats = {
        "posts": published.count(),
        "categories": Category.objects.filter(is_active=True).count(),
        "authors": published.values("author").distinct().count(),
        "views": published.aggregate(s=Sum("views"))["s"] or 0,
    }
    return render(request, "Home_Module/index.html", {
        "featured": featured,
        "side_featured": side_featured,
        "latest_posts": latest,
        "categories": categories,
        "stats": stats,
    })
