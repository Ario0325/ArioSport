import io
import os
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        from django.core.exceptions import ValidationError
        raise ValidationError(
            f"فرمت فایل مجاز نیست. فرمت‌های مجاز: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        )


def validate_image_size(value):
    max_mb = getattr(settings, "IMAGE_UPLOAD_MAX_SIZE_MB", 10)
    if value.size > max_mb * 1024 * 1024:
        from django.core.exceptions import ValidationError
        raise ValidationError(f"حجم فایل نباید بیشتر از {max_mb} مگابایت باشد.")


def compress_image(image_field_file):
    if not image_field_file:
        return

    try:
        image_field_file.open()
        img = Image.open(image_field_file)
    except Exception:
        return

    img = ImageOps.exif_transpose(img)

    max_w = getattr(settings, "IMAGE_UPLOAD_MAX_WIDTH", 1920)
    max_h = getattr(settings, "IMAGE_UPLOAD_MAX_HEIGHT", 1080)
    quality = getattr(settings, "IMAGE_UPLOAD_QUALITY", 82)

    if img.width > max_w or img.height > max_h:
        img.thumbnail((max_w, max_h), Image.LANCZOS)

    has_alpha = img.mode in ("RGBA", "LA", "PA")
    if img.mode == "P":
        img = img.convert("RGBA")
        has_alpha = True

    ext = os.path.splitext(image_field_file.name)[1].lower()
    buf = io.BytesIO()

    if ext in (".jpg", ".jpeg"):
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        new_name = os.path.splitext(image_field_file.name)[0] + ".jpg"
    elif ext == ".png":
        if not has_alpha and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buf, format="PNG", optimize=True)
        new_name = image_field_file.name
    elif ext == ".webp":
        if not has_alpha and img.mode != "RGB":
            img = img.convert("RGB")
        img.save(buf, format="WEBP", quality=quality, method=6)
        new_name = image_field_file.name
    else:
        return

    new_content = ContentFile(buf.getvalue())
    if new_content.size < image_field_file.size:
        image_field_file.save(new_name, new_content, save=False)
