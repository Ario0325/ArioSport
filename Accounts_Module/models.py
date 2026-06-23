from django.db import models
from django.contrib.auth.models import User
from Core_Module.utils import compress_image, validate_image_extension, validate_image_size


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
