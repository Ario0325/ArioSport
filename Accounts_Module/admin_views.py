from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models import ProtectedError
from django.utils import timezone

from Blog_Module.models import Post, Comment, Tag
from Category_Module.models import Category
from Core_Module.models import SiteSetting, ContactMessage, NewsletterSubscriber
from .admin_forms import (AdminPostForm, AdminCategoryForm,
                          AdminSiteSettingForm, AdminUserForm, AdminTagForm)

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff,
                                  login_url="accounts:login")


@staff_required
def dashboard(request):
    published = Post.published.all()
    post_agg = Post.objects.aggregate(
        total=Count("id"),
        published_count=Count("id", filter=Q(status="published")),
        draft_count=Count("id", filter=Q(status="draft")),
        total_views=Sum("views"),
    )
    stats = {
        "posts": post_agg["total"],
        "published": post_agg["published_count"],
        "drafts": post_agg["draft_count"],
        "categories": Category.objects.count(),
        "comments": Comment.objects.count(),
        "pending_comments": Comment.objects.filter(is_approved=False).count(),
        "users": User.objects.count(),
        "messages": ContactMessage.objects.count(),
        "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
        "subscribers": NewsletterSubscriber.objects.count(),
        "total_views": post_agg["total_views"] or 0,
    }
    top_posts = Post.objects.order_by("-views")[:5]
    recent_comments = Comment.objects.select_related("post").order_by("-created_at")[:6]
    recent_posts = Post.objects.select_related("category", "author").order_by("-created_at")[:6]
    cat_stats = (Category.objects.annotate(n=Count("posts")).order_by("-n")[:6])
    return render(request, "Accounts_Module/admin/admin_dashboard.html", {
        "stats": stats, "top_posts": top_posts, "recent_comments": recent_comments,
        "recent_posts": recent_posts, "cat_stats": cat_stats, "active": "dashboard",
    })


# ---------------- Posts ----------------
@staff_required
def post_list(request):
    qs = Post.objects.select_related("category", "author").order_by("-created_at")
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if status:
        qs = qs.filter(status=status)
    posts = Paginator(qs, 12).get_page(request.GET.get("page"))
    return render(request, "Accounts_Module/admin/admin_posts.html", {
        "posts": posts, "q": q, "status": status, "active": "posts",
    })


@staff_required
def post_create(request):
    if request.method == "POST":
        form = AdminPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            messages.success(request, "مقاله جدید ایجاد شد.")
            return redirect("panel:posts")
    else:
        form = AdminPostForm()
    return render(request, "Accounts_Module/admin/admin_post_form.html", {
        "form": form, "active": "posts", "is_new": True,
    })


@staff_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = AdminPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "مقاله بروزرسانی شد.")
            return redirect("panel:posts")
    else:
        form = AdminPostForm(instance=post)
    return render(request, "Accounts_Module/admin/admin_post_form.html", {
        "form": form, "post": post, "active": "posts", "is_new": False,
    })


@staff_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        post.delete()
        messages.success(request, "مقاله حذف شد.")
        return redirect("panel:posts")
    return render(request, "Accounts_Module/admin/admin_confirm_delete.html", {
        "object": post, "title": "حذف مقاله", "name": post.title,
        "cancel_url": "panel:posts", "active": "posts",
    })


# ---------------- Categories ----------------
@staff_required
def category_list(request):
    cats = Category.objects.annotate(n=Count("posts")).order_by("order", "name")
    return render(request, "Accounts_Module/admin/admin_categories.html", {
        "categories": cats, "active": "categories",
    })


@staff_required
def category_create(request):
    if request.method == "POST":
        form = AdminCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "دسته‌بندی ایجاد شد.")
            return redirect("panel:categories")
    else:
        form = AdminCategoryForm()
    return render(request, "Accounts_Module/admin/admin_category_form.html", {
        "form": form, "active": "categories", "is_new": True,
    })


@staff_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = AdminCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "دسته‌بندی بروزرسانی شد.")
            return redirect("panel:categories")
    else:
        form = AdminCategoryForm(instance=cat)
    return render(request, "Accounts_Module/admin/admin_category_form.html", {
        "form": form, "category": cat, "active": "categories", "is_new": False,
    })


@staff_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        try:
            cat.delete()
            messages.success(request, "دسته‌بندی حذف شد.")
        except ProtectedError:
            messages.error(request, "این دسته دارای مقاله است و قابل حذف نیست.")
        return redirect("panel:categories")
    return render(request, "Accounts_Module/admin/admin_confirm_delete.html", {
        "object": cat, "title": "حذف دسته‌بندی", "name": cat.name,
        "cancel_url": "panel:categories", "active": "categories",
    })


# ---------------- Comments ----------------
@staff_required
def comment_list(request):
    qs = Comment.objects.select_related("post", "user").order_by("-created_at")
    f = request.GET.get("filter", "")
    if f == "pending":
        qs = qs.filter(is_approved=False)
    elif f == "approved":
        qs = qs.filter(is_approved=True)
    comments = Paginator(qs, 15).get_page(request.GET.get("page"))
    return render(request, "Accounts_Module/admin/admin_comments.html", {
        "comments": comments, "filter": f, "active": "comments",
    })


@staff_required
def comment_approve(request, pk):
    c = get_object_or_404(Comment, pk=pk)
    if request.method == "POST":
        c.is_approved = not c.is_approved
        c.save()
        messages.success(request, "وضعیت دیدگاه تغییر کرد.")
    return redirect(request.META.get("HTTP_REFERER", "panel:comments"))


@staff_required
def comment_delete(request, pk):
    c = get_object_or_404(Comment, pk=pk)
    if request.method == "POST":
        c.delete()
        messages.success(request, "دیدگاه حذف شد.")
    return redirect(request.META.get("HTTP_REFERER", "panel:comments"))


# ---------------- Users ----------------
@staff_required
def user_list(request):
    qs = User.objects.select_related("profile").order_by("-date_joined")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) |
                       Q(first_name__icontains=q) | Q(last_name__icontains=q))
    users = Paginator(qs, 15).get_page(request.GET.get("page"))
    return render(request, "Accounts_Module/admin/admin_users.html", {
        "users": users, "q": q, "active": "users",
    })


@staff_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = AdminUserForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user.first_name = cd["first_name"]
            user.last_name = cd["last_name"]
            user.email = cd["email"]
            user.is_staff = cd["is_staff"]
            user.is_active = cd["is_active"]
            user.save()
            messages.success(request, "کاربر بروزرسانی شد.")
            return redirect("panel:users")
    else:
        form = AdminUserForm(initial={
            "first_name": user.first_name, "last_name": user.last_name,
            "email": user.email, "is_staff": user.is_staff, "is_active": user.is_active,
        })
    return render(request, "Accounts_Module/admin/admin_user_form.html", {
        "form": form, "edit_user": user, "active": "users",
    })


@staff_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        if user == request.user:
            messages.error(request, "نمی‌توانید حساب خودتان را حذف کنید.")
        else:
            user.delete()
            messages.success(request, "کاربر حذف شد.")
        return redirect("panel:users")
    return render(request, "Accounts_Module/admin/admin_confirm_delete.html", {
        "object": user, "title": "حذف کاربر",
        "name": user.get_full_name() or user.username,
        "cancel_url": "panel:users", "active": "users",
    })


# ---------------- Messages ----------------
@staff_required
def message_list(request):
    qs = ContactMessage.objects.order_by("-created_at")
    msgs = Paginator(qs, 15).get_page(request.GET.get("page"))
    return render(request, "Accounts_Module/admin/admin_messages.html", {
        "msgs": msgs, "active": "messages",
    })


@staff_required
def message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if not msg.is_read:
        msg.is_read = True
        msg.save()
    return render(request, "Accounts_Module/admin/admin_message_detail.html", {
        "msg": msg, "active": "messages",
    })


@staff_required
def message_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        msg.delete()
        messages.success(request, "پیام حذف شد.")
        return redirect("panel:messages")
    return render(request, "Accounts_Module/admin/admin_confirm_delete.html", {
        "object": msg, "title": "حذف پیام", "name": msg.subject,
        "cancel_url": "panel:messages", "active": "messages",
    })


# ---------------- Settings ----------------
@staff_required
def settings_view(request):
    site = SiteSetting.load()
    if request.method == "POST":
        form = AdminSiteSettingForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات سایت ذخیره شد.")
            return redirect("panel:settings")
    else:
        form = AdminSiteSettingForm(instance=site)
    return render(request, "Accounts_Module/admin/admin_settings.html", {
        "form": form, "active": "settings",
    })


# ---------------- Tags ----------------
@staff_required
def tag_list(request):
    qs = Tag.objects.annotate(n=Count("posts")).order_by("name")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    tags = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "Accounts_Module/admin/admin_tags.html", {
        "tags": tags, "q": q, "active": "tags",
    })


@staff_required
def tag_create(request):
    if request.method == "POST":
        form = AdminTagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "برچسب جدید ایجاد شد.")
            return redirect("panel:tags")
    else:
        form = AdminTagForm()
    return render(request, "Accounts_Module/admin/admin_tag_form.html", {
        "form": form, "active": "tags", "is_new": True,
    })


@staff_required
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        form = AdminTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, "برچسب بروزرسانی شد.")
            return redirect("panel:tags")
    else:
        form = AdminTagForm(instance=tag)
    return render(request, "Accounts_Module/admin/admin_tag_form.html", {
        "form": form, "tag": tag, "active": "tags", "is_new": False,
    })


@staff_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        tag.delete()
        messages.success(request, "برچسب حذف شد.")
        return redirect("panel:tags")
    return render(request, "Accounts_Module/admin/admin_confirm_delete.html", {
        "object": tag, "title": "حذف برچسب", "name": tag.name,
        "cancel_url": "panel:tags", "active": "tags",
    })
