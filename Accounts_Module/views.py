from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, LoginForm, EditProfileForm


def _safe_redirect(request, fallback):
    nxt = request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(fallback)


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("panel:dashboard")
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "با موفقیت وارد شدید!")
            nxt = request.POST.get("next") or request.GET.get("next")
            if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                return redirect(nxt)
            if form.get_user().is_staff:
                return redirect("panel:dashboard")
            return redirect("accounts:dashboard")
    else:
        form = LoginForm(request)
    return render(request, "Accounts_Module/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "حساب شما با موفقیت ساخته شد!")
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()
    return render(request, "Accounts_Module/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "از حساب خود خارج شدید.")
    return redirect("home:index")


@login_required
def dashboard(request):
    from Blog_Module.models import Comment
    my_comments = Comment.objects.filter(user=request.user).select_related("post")[:10]
    return render(request, "Accounts_Module/dashboard.html", {
        "my_comments": my_comments,
        "comment_count": Comment.objects.filter(user=request.user).count(),
    })


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "پروفایل شما بروزرسانی شد.")
            return redirect("accounts:dashboard")
    else:
        form = EditProfileForm(instance=profile)
    return render(request, "Accounts_Module/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "رمز عبور شما تغییر کرد.")
            return redirect("accounts:dashboard")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "Accounts_Module/change_password.html", {"form": form})
