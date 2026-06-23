import math
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from Category_Module.models import Category
from ckeditor_uploader.fields import RichTextUploadingField
from Core_Module.utils import compress_image, validate_image_extension, validate_image_size


class Tag(models.Model):
    name = models.CharField("نام برچسب", max_length=60, unique=True)
    slug = models.SlugField("اسلاگ", max_length=80, unique=True, blank=True, allow_unicode=True)

    class Meta:
        verbose_name = "برچسب"
        verbose_name_plural = "برچسب‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag", kwargs={"slug": self.slug})


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status="published")


class Post(models.Model):
    STATUS_CHOICES = [
        ("draft", "پیش‌نویس"),
        ("published", "منتشر شده"),
    ]
    title = models.CharField("عنوان", max_length=220)
    slug = models.SlugField("اسلاگ", max_length=255, unique=True, blank=True, allow_unicode=True)
    category = models.ForeignKey(Category, verbose_name="دسته‌بندی", on_delete=models.PROTECT,
                                 related_name="posts")
    author = models.ForeignKey(User, verbose_name="نویسنده", on_delete=models.SET_NULL,
                               null=True, related_name="posts")
    excerpt = models.TextField("خلاصه", max_length=400, blank=True,
                               help_text="چکیده کوتاه که در کارت مقاله نمایش داده می‌شود.")
    content = RichTextUploadingField("متن کامل مقاله", config_name="default")
    cover_image = models.ImageField("تصویر شاخص", upload_to="posts/%Y/%m/", blank=True, null=True,
                                     validators=[validate_image_extension, validate_image_size])
    tags = models.ManyToManyField(Tag, verbose_name="برچسب‌ها", blank=True, related_name="posts")

    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default="draft")
    is_featured = models.BooleanField("مطلب ویژه", default=False)
    reading_time = models.PositiveIntegerField("زمان مطالعه (دقیقه)", default=0)
    views = models.PositiveIntegerField("بازدید", default=0)

    published_at = models.DateTimeField("تاریخ انتشار", blank=True, null=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["-published_at"]), models.Index(fields=["status"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "post"
            slug, n = base, 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        # auto reading time (~200 wpm)
        words = len(strip_tags(self.content).split())
        self.reading_time = max(1, math.ceil(words / 200))
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()
        # Compress cover image on upload/change
        if self.cover_image:
            try:
                old = Post.objects.get(pk=self.pk).cover_image if self.pk else None
            except Post.DoesNotExist:
                old = None
            if old != self.cover_image:
                compress_image(self.cover_image)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    @property
    def author_name(self):
        if self.author:
            full = self.author.get_full_name()
            return full or self.author.username
        return "ناشناس"

    @property
    def author_initial(self):
        return (self.author_name or "؟").strip()[:1]

    @property
    def approved_comments(self):
        return self.comments.filter(is_approved=True, parent__isnull=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, verbose_name="مقاله", on_delete=models.CASCADE,
                             related_name="comments")
    user = models.ForeignKey(User, verbose_name="کاربر", on_delete=models.SET_NULL,
                             null=True, blank=True, related_name="comments")
    parent = models.ForeignKey("self", verbose_name="پاسخ به", on_delete=models.CASCADE,
                               null=True, blank=True, related_name="replies")
    name = models.CharField("نام", max_length=120)
    email = models.EmailField("ایمیل", blank=True)
    body = models.TextField("متن دیدگاه")
    is_approved = models.BooleanField("تایید شده", default=False)
    created_at = models.DateTimeField("تاریخ", auto_now_add=True)

    class Meta:
        verbose_name = "دیدگاه"
        verbose_name_plural = "دیدگاه‌ها"
        ordering = ["created_at"]

    def __str__(self):
        return f"دیدگاه {self.name} بر {self.post}"

    @property
    def initial(self):
        return (self.name or "؟").strip()[:1]
