from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, LoginForm, EditProfileForm, OTPVerificationForm, PasswordChangeRequestForm, PasswordResetRequestForm, CustomSetPasswordForm
from .models import EmailOTP
from .n8n_utils import send_auth_event


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
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "حساب شما هنوز فعال نشده است. لطفاً ابتدا ایمیل خود را تایید کنید.")
                return redirect("accounts:login")
            login(request, user)
            messages.success(request, "با موفقیت وارد شدید!")
            nxt = request.POST.get("next") or request.GET.get("next")
            if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                return redirect(nxt)
            if user.is_staff:
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
            email = form.cleaned_data["email"]
            existing = User.objects.filter(email__iexact=email, is_active=False).first()

            if existing:
                user = existing
                full = form.cleaned_data["full_name"].strip()
                first, _, last = full.partition(" ")
                user.first_name = first
                user.last_name = last
                user.set_password(form.cleaned_data["password"])
                user.save()
            else:
                user = form.save(commit=False)
                user.is_active = False
                user.save()

            otp = EmailOTP.create_otp(
                email=user.email,
                purpose="register",
                user=user,
                expiry_minutes=15,
            )

            send_auth_event(
                event="register",
                email=user.email,
                username=user.get_full_name() or user.username,
                code=otp.code,
            )

            request.session["otp_email"] = user.email
            request.session["otp_purpose"] = "register"
            return redirect("accounts:verify_otp")
    else:
        form = RegisterForm()
    return render(request, "Accounts_Module/register.html", {"form": form})


def verify_otp(request):
    email = request.session.get("otp_email")
    purpose = request.session.get("otp_purpose", "register")

    if not email:
        messages.error(request, "لطفاً ابتدا ثبت‌نام کنید.")
        return redirect("accounts:register")

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if EmailOTP.verify(email=email, code=code, purpose=purpose):
                if purpose == "register":
                    user = get_object_or_404(User, email__iexact=email, is_active=False)
                    user.is_active = True
                    user.save(update_fields=["is_active"])
                    login(request, user)
                    del request.session["otp_email"]
                    del request.session["otp_purpose"]
                    messages.success(request, "حساب شما با موفقیت فعال شد!")
                    return redirect("accounts:dashboard")
                elif purpose == "password_reset":
                    request.session["otp_verified"] = True
                    request.session["reset_email"] = email
                    del request.session["otp_email"]
                    del request.session["otp_purpose"]
                    return redirect("accounts:password_reset_set_new")
            else:
                messages.error(request, "کد تایید نامعتبر یا منقضی شده است.")
    else:
        form = OTPVerificationForm()

    remaining = EmailOTP.objects.filter(
        email__iexact=email, purpose=purpose, is_used=False
    ).count()

    return render(request, "Accounts_Module/verify_otp.html", {
        "form": form,
        "email": email,
        "purpose": purpose,
        "remaining_otps": remaining,
    })


def resend_otp(request):
    email = request.session.get("otp_email")
    purpose = request.session.get("otp_purpose", "register")

    if not email:
        messages.error(request, "لطفاً ابتدا ثبت‌نام کنید.")
        return redirect("accounts:register")

    user = User.objects.filter(email__iexact=email).first()
    username = user.get_full_name() if user else email

    otp = EmailOTP.create_otp(email=email, purpose=purpose, user=user, expiry_minutes=15)

    send_auth_event(
        event="register" if purpose == "register" else "password_reset",
        email=email,
        username=username,
        code=otp.code,
    )

    messages.success(request, "کد تایید جدید به ایمیل شما ارسال شد.")
    return redirect("accounts:verify_otp")


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
    if not request.session.get("otp_verified"):
        if request.method == "POST":
            form = PasswordChangeRequestForm(request.POST)
            if form.is_valid():
                otp = EmailOTP.create_otp(
                    email=request.user.email,
                    purpose="password_reset",
                    user=request.user,
                    expiry_minutes=15,
                )
                send_auth_event(
                    event="password_reset",
                    email=request.user.email,
                    username=request.user.get_full_name() or request.user.username,
                    code=otp.code,
                )
                request.session["otp_email"] = request.user.email
                request.session["otp_purpose"] = "password_reset"
                return redirect("accounts:verify_otp")
        else:
            form = PasswordChangeRequestForm()
        return render(request, "Accounts_Module/change_password_request.html", {"form": form})

    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            request.session.pop("otp_verified", None)
            messages.success(request, "رمز عبور شما تغییر کرد.")
            return redirect("accounts:dashboard")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "Accounts_Module/change_password.html", {"form": form})


def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email__iexact=email, is_active=True).first()

            if user:
                otp = EmailOTP.create_otp(
                    email=email,
                    purpose="password_reset",
                    user=user,
                    expiry_minutes=15,
                )
                send_auth_event(
                    event="password_reset",
                    email=email,
                    username=user.get_full_name() or user.username,
                    code=otp.code,
                )

            request.session["otp_email"] = email
            request.session["otp_purpose"] = "password_reset"
            return redirect("accounts:verify_otp")
    else:
        form = PasswordResetRequestForm()
    return render(request, "Accounts_Module/password_reset.html", {"form": form})


def password_reset_set_new(request):
    if not request.session.get("otp_verified") or not request.session.get("reset_email"):
        messages.error(request, "لطفاً ابتدا ایمیل خود را تایید کنید.")
        return redirect("accounts:password_reset")

    email = request.session["reset_email"]
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(request, "کاربری با این ایمیل یافت نشد.")
        return redirect("accounts:password_reset")

    if request.method == "POST":
        form = CustomSetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            request.session.pop("otp_verified", None)
            request.session.pop("reset_email", None)
            messages.success(request, "رمز عبور شما با موفقیت تغییر کرد. اکنون می‌توانید وارد شوید.")
            return redirect("accounts:login")
    else:
        form = CustomSetPasswordForm(user)
    return render(request, "Accounts_Module/password_reset_confirm.html", {"form": form})
