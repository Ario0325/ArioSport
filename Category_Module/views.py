from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category


def category_list(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, "Category_Module/category_list.html", {
        "categories": categories,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    posts_qs = category.posts.filter(status="published").select_related("author", "category")
    paginator = Paginator(posts_qs, 6)
    page = request.GET.get("page")
    posts = paginator.get_page(page)
    return render(request, "Category_Module/category_detail.html", {
        "category": category,
        "posts": posts,
    })
