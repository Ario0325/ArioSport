import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from Core_Module.utils import compress_image, validate_image_extension, validate_image_size


class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ("register", "ثبت‌نام"),
        ("password_reset", "بازیابی رمز عبور"),
    ]

    email = models.EmailField("ایمیل", db_index=True)
    code = models.CharField("کد تایید", max_length=6)
    purpose = models.CharField("هدف", max_length=20, choices=PURPOSE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                             related_name="otps")
    is_used = models.BooleanField("استفاده شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField("تاریخ انقضا")

    class Meta:
        verbose_name = "کد تایید"
        verbose_name_plural = "کدهای تایید"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.code} ({self.purpose})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    @classmethod
    def generate_code(cls):
        return f"{random.randint(100000, 999999)}"

    @classmethod
    def create_otp(cls, email, purpose, user=None, expiry_minutes=15):
        cls.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)
        code = cls.generate_code()
        otp = cls.objects.create(
            email=email,
            code=code,
            purpose=purpose,
            user=user,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
        )
        return otp

    @classmethod
    def verify(cls, email, code, purpose):
        otp = cls.objects.filter(
            email__iexact=email, code=code, purpose=purpose, is_used=False
        ).order_by("-created_at").first()
        if otp and not otp.is_expired:
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            return True
        return False


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField("تصویر پروفایل", upload_to="avatars/", blank=True, null=True,
                                validators=[validate_image_extension, validate_image_size])
    bio = models.TextField("بیوگرافی", blank=True)
    role = models.CharField("سمت / تخصص", max_length=120, blank=True,
                            default="عضو آریو اسپورت")
    phone = models.CharField("تلفن", max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"

    def __str__(self):
        return f"پروفایل {self.user.username}"

    def save(self, *args, **kwargs):
        if self.avatar:
            try:
                old = Profile.objects.get(pk=self.pk).avatar if self.pk else None
            except Profile.DoesNotExist:
                old = None
            if old != self.avatar:
                compress_image(self.avatar)
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def initial(self):
        return self.display_name.strip()[:1]
