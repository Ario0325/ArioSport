from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("نام دسته", max_length=80, unique=True)
    slug = models.SlugField("اسلاگ", max_length=100, unique=True, blank=True, allow_unicode=True)
    description = models.TextField("توضیحات", blank=True)
    icon = models.CharField("آیکون (Lucide)", max_length=40, default="layout-grid",
                            help_text="نام آیکون از کتابخانه Lucide مثل: goal, dribbble, dumbbell")
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("category:detail", kwargs={"slug": self.slug})

    @property
    def published_post_count(self):
        return self.posts.filter(status="published").count()
