import json
import os
import shutil
import zipfile
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from Blog_Module.models import Post, Tag
from Category_Module.models import Category


class Command(BaseCommand):
    help = "Import posts from a zip file exported by export_posts"

    def add_arguments(self, parser):
        parser.add_argument("zip_path", help="Path to the exported zip file")
        parser.add_argument(
            "--update",
            action="store_true",
            default=False,
            help="Update existing posts (match by slug)",
        )

    def handle(self, *args, **opts):
        zip_path = opts["zip_path"]
        update = opts["update"]

        if not os.path.isfile(zip_path):
            self.stderr.write(self.style.ERROR(f"File not found: {zip_path}"))
            return

        tmp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_dir)

            json_path = os.path.join(tmp_dir, "data.json")
            if not os.path.isfile(json_path):
                self.stderr.write(self.style.ERROR("Invalid export: data.json not found."))
                return

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            images_dir = os.path.join(tmp_dir, "images")
            media_root = settings.MEDIA_ROOT

            created_cat = 0
            for cat_data in data.get("categories", []):
                _, created = Category.objects.update_or_create(
                    slug=cat_data["slug"],
                    defaults={
                        "name": cat_data["name"],
                        "description": cat_data.get("description", ""),
                        "icon": cat_data.get("icon", "layout-grid"),
                        "order": cat_data.get("order", 0),
                        "is_active": cat_data.get("is_active", True),
                    },
                )
                if created:
                    created_cat += 1

            created_tag = 0
            for tag_data in data.get("tags", []):
                _, created = Tag.objects.update_or_create(
                    slug=tag_data["slug"],
                    defaults={"name": tag_data["name"]},
                )
                if created:
                    created_tag += 1

            default_author = User.objects.filter(is_superuser=True).first()

            created_post = 0
            updated_post = 0
            skipped_post = 0

            for post_data in data.get("posts", []):
                slug = post_data["slug"]
                exists = Post.objects.filter(slug=slug).exists()

                if exists and not update:
                    skipped_post += 1
                    continue

                category = None
                if post_data.get("category_slug"):
                    category = Category.objects.filter(slug=post_data["category_slug"]).first()

                author = default_author
                if post_data.get("author_username"):
                    author = User.objects.filter(username=post_data["author_username"]).first() or default_author

                cover_image_path = None
                if post_data.get("cover_image"):
                    src_img = os.path.join(images_dir, os.path.basename(post_data["cover_image"]))
                    if os.path.isfile(src_img):
                        dst_dir = os.path.join(media_root, os.path.dirname(post_data["cover_image"]))
                        os.makedirs(dst_dir, exist_ok=True)
                        dst_img = os.path.join(media_root, post_data["cover_image"])
                        if not os.path.isfile(dst_img):
                            shutil.copy2(src_img, dst_img)
                        cover_image_path = post_data["cover_image"]

                published_at = None
                if post_data.get("published_at"):
                    published_at = timezone.datetime.fromisoformat(post_data["published_at"])
                    if timezone.is_naive(published_at):
                        published_at = timezone.make_aware(published_at)

                tag_slugs = post_data.get("tags", [])

                if exists:
                    post = Post.objects.get(slug=slug)
                    post.title = post_data["title"]
                    post.category = category
                    post.author = author
                    post.excerpt = post_data.get("excerpt", "")
                    post.content = post_data["content"]
                    if cover_image_path:
                        post.cover_image = cover_image_path
                    post.status = post_data.get("status", "draft")
                    post.is_featured = post_data.get("is_featured", False)
                    post.views = post_data.get("views", 0)
                    if published_at:
                        post.published_at = published_at
                    post.save()
                    updated_post += 1
                else:
                    post = Post.objects.create(
                        title=post_data["title"],
                        slug=slug,
                        category=category,
                        author=author,
                        excerpt=post_data.get("excerpt", ""),
                        content=post_data["content"],
                        cover_image=cover_image_path or "",
                        status=post_data.get("status", "draft"),
                        is_featured=post_data.get("is_featured", False),
                        views=post_data.get("views", 0),
                        published_at=published_at,
                    )
                    created_post += 1

                if tag_slugs:
                    tags = Tag.objects.filter(slug__in=tag_slugs)
                    post.tags.set(tags)

            self.stdout.write(self.style.SUCCESS(
                f"Done! Created: {created_post}, Updated: {updated_post}, Skipped: {skipped_post}, "
                f"Categories: {created_cat} new, Tags: {created_tag} new"
            ))

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
