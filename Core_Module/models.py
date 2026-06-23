from django.db import models
from django.core.exceptions import ValidationError
from .utils import compress_image, validate_image_extension, validate_image_size


class SiteSetting(models.Model):
    """Singleton model holding global site configuration."""
    site_name = models.CharField("نام سایت", max_length=100, default="ArioSport")
    tagline = models.CharField("شعار", max_length=200, blank=True,
                               default="مرجع حرفه‌ای اخبار و تحلیل‌های ورزشی")
    about_short = models.TextField("درباره کوتاه (فوتر)", blank=True,
        default="مرجع حرفه‌ای اخبار، تحلیل و مقالات ورزشی. ما با اشتیاق، دنیای ورزش را برای شما روایت می‌کنیم.")
    about_full = models.TextField("متن کامل صفحه درباره ما", blank=True)
    logo = models.ImageField("لوگو", upload_to="site/", blank=True, null=True,
                              validators=[validate_image_extension, validate_image_size])
    favicon = models.ImageField("فاوآیکون", upload_to="site/", blank=True, null=True,
                                 validators=[validate_image_extension, validate_image_size])

    email = models.EmailField("ایمیل تماس", blank=True, default="info@ariosport.local")
    phone = models.CharField("تلفن", max_length=40, blank=True)
    address = models.CharField("آدرس", max_length=255, blank=True)

    instagram = models.URLField("اینستاگرام", blank=True)
    telegram = models.URLField("تلگرام", blank=True)
    twitter = models.URLField("توییتر", blank=True)
    youtube = models.URLField("یوتیوب", blank=True)

    footer_text = models.CharField("متن کپی‌رایت فوتر", max_length=200, blank=True,
        default="ArioSport — تمامی حقوق محفوظ است.")

    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        if self.logo:
            try:
                old = SiteSetting.objects.get(pk=1).logo
            except SiteSetting.DoesNotExist:
                old = None
            if old != self.logo:
                compress_image(self.logo)
        if self.favicon:
            try:
                old = SiteSetting.objects.get(pk=1).favicon
            except SiteSetting.DoesNotExist:
                old = None
            if old != self.favicon:
                compress_image(self.favicon)
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    name = models.CharField("نام", max_length=120)
    email = models.EmailField("ایمیل")
    subject = models.CharField("موضوع", max_length=200)
    message = models.TextField("متن پیام")
    is_read = models.BooleanField("خوانده شده", default=False)
    created_at = models.DateTimeField("تاریخ ارسال", auto_now_add=True)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject}"


class NewsletterSubscriber(models.Model):
    email = models.EmailField("ایمیل", unique=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ عضویت", auto_now_add=True)

    class Meta:
        verbose_name = "عضو خبرنامه"
        verbose_name_plural = "اعضای خبرنامه"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
