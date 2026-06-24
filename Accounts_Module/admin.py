from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, EmailOTP


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ["email", "code", "purpose", "is_used", "created_at", "expires_at"]
    list_filter = ["purpose", "is_used"]
    search_fields = ["email"]
    readonly_fields = ["code", "created_at"]
    ordering = ["-created_at"]


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)
