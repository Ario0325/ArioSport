from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.contrib import messages
from .models import Post, Tag, Comment
from .forms import CommentForm
from Category_Module.models import Category


def blog_list(request):
    posts_qs = Post.published.select_related("author", "category")
    active_cat = request.GET.get("cat")
    if active_cat:
        posts_qs = posts_qs.filter(category__slug=active_cat)

    paginator = Paginator(posts_qs, 6)
    posts = paginator.get_page(request.GET.get("page"))

    categories = (Category.objects.filter(is_active=True)
                  .annotate(post_count=Count("posts", filter=Q(posts__status="published"))))

    context = {
        "posts": posts,
        "categories": categories,
        "popular_posts": Post.published.order_by("-views")[:3],
        "tags": Tag.objects.all()[:12],
        "active_cat": active_cat,
    }
    return render(request, "Blog_Module/blog_list.html", context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("author", "category").prefetch_related("tags", "comments"),
        slug=slug, status="published",
    )
    # increment views (atomic)
    Post.objects.filter(pk=post.pk).update(views=F("views") + 1)

    related = (Post.published.filter(category=post.category)
               .exclude(pk=post.pk).select_related("author", "category")[:3])

    if request.method == "POST":
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            if request.user.is_authenticated:
                comment.user = request.user
                comment.name = comment.name or request.user.get_full_name() or request.user.username
                comment.email = comment.email or request.user.email
            parent_id = request.POST.get("parent")
            if parent_id:
                try:
                    comment.parent_id = int(parent_id)
                except (ValueError, TypeError):
                    pass
            comment.save()
            messages.success(request, "دیدگاه شما ثبت شد و پس از تایید نمایش داده می‌شود.")
            return redirect(post.get_absolute_url() + "#comments")
    else:
        form = CommentForm(user=request.user)

    context = {
        "post": post,
        "form": form,
        "comments": post.approved_comments.prefetch_related("replies"),
        "related_posts": related,
    }
    return render(request, "Blog_Module/post_detail.html", context)


def search(request):
    query = request.GET.get("q", "").strip()
    results = Post.published.none()
    total = 0
    if query:
        results = Post.published.filter(
            Q(title__icontains=query) | Q(content__icontains=query) |
            Q(excerpt__icontains=query) | Q(tags__name__icontains=query)
        ).distinct().select_related("author", "category")
        total = results.count()
    paginator = Paginator(results, 6)
    posts = paginator.get_page(request.GET.get("page"))
    return render(request, "Blog_Module/search_results.html", {
        "query": query, "posts": posts, "total": total,
    })


def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts_qs = tag.posts.filter(status="published").select_related("author", "category")
    paginator = Paginator(posts_qs, 6)
    posts = paginator.get_page(request.GET.get("page"))
    return render(request, "Blog_Module/blog_list.html", {
        "posts": posts,
        "categories": Category.objects.filter(is_active=True),
        "popular_posts": Post.published.order_by("-views")[:3],
        "tags": Tag.objects.all()[:12],
        "current_tag": tag,
    })
