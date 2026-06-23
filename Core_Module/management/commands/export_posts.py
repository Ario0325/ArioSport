import json
import os
import shutil
import zipfile
from django.core.management.base import BaseCommand
from django.conf import settings
from Blog_Module.models import Post, Tag
from Category_Module.models import Category


class Command(BaseCommand):
    help = "Export posts with images to a zip file for transfer to online server"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="posts_export.zip",
            help="Output zip file path (default: posts_export.zip)",
        )
        parser.add_argument(
            "--status",
            default=None,
            help="Filter by status: published or draft (default: all)",
        )

    def handle(self, *args, **opts):
        output_path = opts["output"]
        status_filter = opts["status"]

        posts_qs = Post.objects.all()
        if status_filter:
            posts_qs = posts_qs.filter(status=status_filter)

        if not posts_qs.exists():
            self.stdout.write(self.style.WARNING("No posts found to export."))
            return

        export_dir = os.path.join(settings.BASE_DIR, "_export_temp")
        images_dir = os.path.join(export_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        categories_data = []
        tags_data = []
        posts_data = []
        copied_images = set()

        for post in posts_qs.select_related("category", "author").prefetch_related("tags"):
            cat = post.category
            if cat and not any(c["slug"] == cat.slug for c in categories_data):
                categories_data.append({
                    "name": cat.name,
                    "slug": cat.slug,
                    "description": cat.description,
                    "icon": cat.icon,
                    "order": cat.order,
                    "is_active": cat.is_active,
                })

            for tag in post.tags.all():
                if not any(t["slug"] == tag.slug for t in tags_data):
                    tags_data.append({"name": tag.name, "slug": tag.slug})

            cover_rel = ""
            if post.cover_image:
                cover_rel = str(post.cover_image)
                src = os.path.join(settings.MEDIA_ROOT, cover_rel)
                if os.path.isfile(src) and cover_rel not in copied_images:
                    dst = os.path.join(images_dir, os.path.basename(cover_rel))
                    shutil.copy2(src, dst)
                    copied_images.add(cover_rel)

            posts_data.append({
                "title": post.title,
                "slug": post.slug,
                "category_slug": cat.slug if cat else "",
                "author_username": post.author.username if post.author else "",
                "excerpt": post.excerpt,
                "content": post.content,
                "cover_image": cover_rel,
                "tags": [t.slug for t in post.tags.all()],
                "status": post.status,
                "is_featured": post.is_featured,
                "views": post.views,
                "published_at": post.published_at.isoformat() if post.published_at else None,
            })

        export_json = {
            "categories": categories_data,
            "tags": tags_data,
            "posts": posts_data,
        }

        json_path = os.path.join(export_dir, "data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_json, f, ensure_ascii=False, indent=2)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(json_path, "data.json")
            for img_name in os.listdir(images_dir):
                zf.write(os.path.join(images_dir, img_name), f"images/{img_name}")

        shutil.rmtree(export_dir)

        self.stdout.write(self.style.SUCCESS(
            f"Exported {len(posts_data)} posts, {len(categories_data)} categories, "
            f"{len(tags_data)} tags, {len(copied_images)} images → {output_path}"
        ))
