from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from .forms import ContactForm, NewsletterForm


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /django-admin/",
        "Disallow: /ckeditor/",
        "Disallow: /accounts/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def about(request):
    return render(request, "Core_Module/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "پیام شما با موفقیت ارسال شد!")
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "Core_Module/contact.html", {"form": form})


def newsletter_subscribe(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "عضویت شما در خبرنامه ثبت شد!")
        else:
            messages.info(request, "این ایمیل قبلاً ثبت شده یا نامعتبر است.")
    return redirect(request.META.get("HTTP_REFERER", "home:index"))


# ---- Error handlers ----
def error_403(request, exception=None):
    return render(request, "Core_Module/403.html", status=403)


def error_404(request, exception=None):
    return render(request, "Core_Module/404.html", status=404)


def error_500(request):
    return render(request, "Core_Module/500.html", status=500)
