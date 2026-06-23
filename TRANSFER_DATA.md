# انتقال مقالات از لوکال به سایت آنلاین

## خلاصه

دو دستور مدیریتی Django ساخته شده:
- `export_posts` — خروجی گرفتن از مقالات + تصاویر (فایل zip)
- `import_posts` — وارد کردن مقالات + تصاویر در سایت آنلاین

---

## مرحله ۱: خروجی گرفتن از لوکال

در ترمینال لوکال، وارد پوشه پروژه شوید:

```bash
cd C:\Users\Ario\Downloads\ArioSport_Blog\ArioSport_Blog
python manage.py export_posts --output my_posts.zip
```

**فیلتر بر اساس وضعیت (اختیاری):**
```bash
# فقط مقالات منتشر شده
python manage.py export_posts --output my_posts.zip --status published

# فقط پیش‌نویس‌ها
python manage.py export_posts --output my_posts.zip --status draft
```

خروجی: فایل `my_posts.zip` در همان پوشه ساخته می‌شود.
این فایل شامل:
- `data.json` — اطلاعات تمام مقالات، دسته‌بندی‌ها و برچسب‌ها
- `images/` — تمام تصاویر شاخص مقالات

---

## مرحله ۲: آپلود فایل zip روی PythonAnywhere

### روش اول: از طریق Files
1. وارد PythonAnywhere شوید
2. از منوی **Files** به مسیر `/home/ArioSport/ArioSport/` بروید
3. فایل `my_posts.zip` را آپلود کنید

### روش دوم: از طریق Bash
اگر فایل را جای دیگری آپلود کردید، آن را به پوشه پروژه منتقل کنید:
```bash
mv /home/ArioSport/my_posts.zip /home/ArioSport/ArioSport/my_posts.zip
```

---

## مرحله ۳: اجرای ایمپورت روی PythonAnywhere

در ترمینال Bash:

```bash
cd /home/ArioSport/ArioSport
source venv/bin/activate
python manage.py import_posts my_posts.zip
```

**برای آپدیت مقالات موجود (اگر قبلاً ایمپورت کرده‌اید):**
```bash
python manage.py import_posts my_posts.zip --update
```

---

## توضیحات دستورات

### `export_posts`

| پارامتر | توضیح | پیش‌فرض |
|---------|-------|---------|
| `--output` | نام فایل zip خروجی | `posts_export.zip` |
| `--status` | فیلتر وضعیت: `published` یا `draft` | همه |

### `import_posts`

| پارامتر | توضیح | پیش‌فرض |
|---------|-------|---------|
| `zip_path` | مسیر فایل zip (اجباری) | — |
| `--update` | آپدیت مقالات موجود (بر اساس slug) | غیرفعال |

---

## نکات مهم

- **تصاویر** به صورت خودکار به مسیر `media/posts/` منتقل می‌شوند
- **دسته‌بندی‌ها** اگر وجود نداشته باشند ساخته می‌شوند
- **برچسب‌ها** اگر وجود نداشته باشند ساخته می‌شوند
- **نویسنده**: اگر نویسنده با همان نام کاربری در سایت آنلاین وجود داشته باشد، همان استفاده می‌شود. در غیر این صورت، نویسنده پیش‌فرض (اولین سوپریوزر) انتخاب می‌شود
- بدون `--update`، مقالاتی که slug تکراری دارند رد می‌شوند

---

## مثال کامل

```bash
# === روی لوکال ===
cd C:\Users\Ario\Downloads\ArioSport_Blog\ArioSport_Blog
python manage.py export_posts --output ariosport_data.zip --status published

# فایل ariosport_data.zip را از طریق Files در PythonAnywhere آپلود کنید

# === روی PythonAnywhere (Bash) ===
cd /home/ArioSport/ArioSport
source venv/bin/activate
python manage.py import_posts ariosport_data.zip
```

بعد از ایمپورت، سایت آنلاین را **Reload** کنید (از بخش Web).
