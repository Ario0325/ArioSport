# راهنمای راه‌اندازی اتوماسیون «ربات تلگرام + Gemini → انتشار مقاله» در ArioSport

> این اتوماسیون در n8n شما ساخته شد:
> **نام:** ArioSport — Telegram AI Article Generator
> **لینک:** https://ariosport.app.n8n.cloud/workflow/x5QX742XSB97nyiw
> **Workflow ID:** `x5QX742XSB97nyiw`

این فایل دقیقاً صفر تا صد می‌گوید چه کارهایی باید انجام دهی و چه چیزهایی اضافه کنی تا اتوماسیون کار کند.

---

## ۱) این اتوماسیون چه کار می‌کند؟

تو در تلگرام به ربات یک پیام می‌دهی که شامل **دسته‌بندی** و **موضوع** مقاله است. سپس:

```
┌──────────────┐   ┌─────────────┐   ┌───────────────┐   ┌───────────────┐
│  Telegram    │──▶│ Parse Input │──▶│ Write Article │──▶│ Format        │
│  Trigger     │   │ (Code)      │   │ (Gemini متن)  │   │ Article (Code)│
└──────────────┘   └─────────────┘   └───────────────┘   └──────┬────────┘
                                                                 │
                                                                 ▼
                    ┌────────────────────┐   ┌──────────────────────────┐
                    │ Notify on Telegram │◀──│ Create Post (Django API) │◀── Generate
                    │ (پیام تأیید)       │   │ (HTTP، multipart)        │    Cover Image
                    └────────────────────┘   └──────────────────────────┘    (Gemini تصویر)
```

| گره | کارش |
|-----|------|
| **Telegram Trigger** | با هر پیام جدید به ربات اجرا می‌شود |
| **Parse Input** | پیام را به موضوع + دسته‌بندی + `category_id` تبدیل می‌کند |
| **Write Article** | با **Gemini** متن مقاله را به صورت **متن استاندارد (بدون HTML)** می‌نویسد |
| **Format Article** | خروجی JSON جمنای را تمیز می‌کند و پاراگراف‌ها را برای نمایش درست در CKEditor آماده می‌کند |
| **Generate Cover Image** | با **Gemini** تصویر کاور مقاله را تولید می‌کند (داده‌ی باینری) |
| **Create Post (Django)** | پست را با عکس به API جنگوی تو ارسال و منتشر می‌کند |
| **Notify on Telegram** | پیام «منتشر شد + لینک» را به تو برمی‌گرداند |

---

## ۲) پیش‌نیازها (یک‌بار انجام می‌شوند)

تو به این چهار چیز نیاز داری. هر کدام را در بخش مربوطه می‌سازیم:
1. **API در جنگو** (endpoint برای ساخت پست)
2. **توکن ربات تلگرام**
3. **کلید API گوگل جمنای (Google Gemini)**
4. **آدرس عمومی (Public URL) سایت جنگو** — چون n8n تو ابری است (`ariosport.app.n8n.cloud`) و باید بتواند به سرور جنگوی تو وصل شود.

---

## ۳) سمت جنگو — ساخت API (خیلی مهم)

### ۳.۱ نصب Django REST Framework
در محیط مجازی پروژه:
```bash
pip install djangorestframework
```
در `ArioSport/settings.py`:
```python
INSTALLED_APPS = [
    # ... بقیه اپ‌ها ...
    "rest_framework",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}
```

### ۳.۲ ساخت فایل `Blog_Module/api.py`
این فایل را **بساز** (طبق ساختار پروژه‌ات این فایل هنوز وجود ندارد):

```python
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Post, Tag
from Category_Module.models import Category


@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def create_post_api(request):
    """ساخت پست جدید از طریق API. ورودی multipart/form-data برای آپلود عکس."""
    data = request.data

    title = data.get("title")
    category_id = data.get("category_id")
    content = data.get("content")

    if not all([title, category_id, content]):
        return Response(
            {"error": "title, category_id, and content are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response(
            {"error": f"Category with id={category_id} not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    post = Post(
        title=title,
        category=category,
        content=content,
        excerpt=data.get("excerpt", ""),
        status=data.get("status", "draft"),
        is_featured=str(data.get("is_featured", "false")).lower() == "true",
    )

    if "cover_image" in request.FILES:
        post.cover_image = request.FILES["cover_image"]

    post.save()

    tag_names = data.get("tags", "")
    if tag_names:
        for name in tag_names.split(","):
            name = name.strip()
            if name:
                tag, _ = Tag.objects.get_or_create(name=name)
                post.tags.add(tag)

    return Response(
        {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "status": post.status,
            "url": post.get_absolute_url(),
        },
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def list_categories_api(request):
    """لیست دسته‌بندی‌های فعال با ID واقعی آن‌ها."""
    cats = Category.objects.filter(is_active=True).values("id", "name", "slug")
    return Response(list(cats))
```

### ۳.۳ افزودن مسیرها در `ArioSport/urls.py`
```python
from Blog_Module.api import create_post_api, list_categories_api

urlpatterns = [
    # ... مسیرهای موجود ...
    path("api/posts/create/", create_post_api, name="api_create_post"),
    path("api/categories/", list_categories_api, name="api_categories"),
]
```

### ۳.۴ تنظیمات لازم در `settings.py`
```python
# دامنه عمومی n8n / تونل خودت را اضافه کن
ALLOWED_HOSTS = ["your-domain.com", "*.ngrok-free.app"]

# پوشه media قابل نوشتن باشد (برای آپلود عکس)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```
> مطمئن شو یک کاربر **ادمین (is_staff=True)** داری: `python manage.py createsuperuser`

### ۳.۵ پر کردن دسته‌بندی‌ها و بررسی ID واقعی
بعد از اجرای سرور، آدرس زیر را با لاگین ادمین باز کن تا **ID واقعی** هر دسته را ببینی:
```
GET https://your-domain.com/api/categories/
```
اگر ID ها با جدول زیر فرق داشت، در گره **Parse Input** (بخش ۶.۲) `categoryMap` را اصلاح کن.

| ID پیش‌فرض | دسته (فارسی) | Slug |
|----|----------------|------------|
| 1 | فوتبال | football |
| 2 | بسکتبال | basketball |
| 3 | والیبال | volleyball |
| 4 | تنیس | tennis |
| 5 | ورزش‌های رزمی | martial-arts |
| 6 | سایر | other |

### ۳.۶ در دسترس قرار دادن سرور (Public URL) — حتمی
n8n تو ابری است، پس `localhost` به درد نمی‌خورد. یکی از این‌ها را انتخاب کن:

- **ngrok** (برای تست سریع):
  ```bash
  ngrok http 8000
  ```
  آدرسی مثل `https://abcd-12-34.ngrok-free.app` می‌گیری. همان را در گره **Create Post** بگذار و در `ALLOWED_HOSTS` اضافه کن.
- **Cloudflare Tunnel** یا **یک سرور واقعی با دامنه** (برای استفاده دائمی، توصیه‌شده).

---

## ۴) ساخت ربات تلگرام و گرفتن توکن
1. در تلگرام به **@BotFather** پیام بده.
2. دستور `/newbot` → یک نام و یک username (که به `bot` ختم می‌شود) انتخاب کن.
3. توکنی مثل `123456789:AAH...xyz` می‌گیری → این را نگه دار.

---

## ۵) گرفتن کلید API گوگل جمنای (Gemini)
1. به **Google AI Studio** برو: https://aistudio.google.com/apikey
2. روی **Create API key** بزن و کلید را کپی کن.
3. مطمئن شو دسترسی به مدل‌های متن و تصویر (image / nano-banana) فعال است.

---

## ۶) تنظیم گره‌ها در n8n (داخل خود ورک‌فلو)

ورک‌فلو را باز کن: https://ariosport.app.n8n.cloud/workflow/x5QX742XSB97nyiw

### ۶.۱ ساخت سه Credential
در n8n از منوی **Credentials → + Add credential**:

| Credential | نوع در n8n | مقدار |
|------------|------------|-------|
| **Telegram Bot** | *Telegram API* | توکن BotFather (بخش ۴) |
| **Google Gemini** | *Google Gemini (PaLM) API* | کلید جمنای (بخش ۵) |
| **Django Admin Basic Auth** | *Basic Auth* | `User` = نام‌کاربری ادمین، `Password` = رمز ادمین |

سپس هر گره را باز کن و در قسمت **Credential** همان را انتخاب کن:
- گره **Telegram Trigger** و **Notify on Telegram** → *Telegram Bot*
- گره **Write Article** و **Generate Cover Image** → *Google Gemini*
- گره **Create Post (Django)** → *Django Admin Basic Auth*

### ۶.۲ آدرس API را بگذار
گره **Create Post (Django)** را باز کن و در فیلد **URL** عبارت `https://YOUR-DOMAIN.com` را با آدرس عمومی واقعی‌ات عوض کن:
```
https://your-domain.com/api/posts/create/
```

### ۶.۳ انتخاب مدل Gemini
- در **Write Article**: فیلد **Model** را باز کن و یک مدل متنی انتخاب کن (پیش‌فرض `gemini-2.5-flash`). اگر در لیست نبود، نزدیک‌ترین مدل موجود حساب خودت را انتخاب کن.
- در **Generate Cover Image**: مدل تولید تصویر را انتخاب کن (پیش‌فرض `gemini-2.5-flash-image` معروف به *nano banana*). اگر نبود، مدل `imagen` یا مدل تصویری موجود را انتخاب کن.

### ۶.۴ (اختیاری) اصلاح نگاشت دسته‌ها
اگر ID های واقعی (بخش ۳.۵) فرق داشتند، در گره **Parse Input** فقط اعداد داخل `categoryMap` را اصلاح کن.

---

## ۷) فعال‌سازی و اتصال تلگرام
1. بعد از اینکه همه Credential ها و URL ست شدند، بالا-راست ورک‌فلو کلید **Active** را روشن کن.
2. با فعال شدن، n8n به‌صورت خودکار **webhook** ربات تلگرام را ست می‌کند؛ کار دستی دیگری لازم نیست.
3. تمام.

---

## ۸) نحوه استفاده (فرمت پیام در تلگرام)
به ربات یکی از این دو فرمت را بفرست:

**فرمت ۱ — یک خطی (توصیه‌شده):**
```
فوتبال | تحلیل عملکرد تیم ملی ایران در جام جهانی
```

**فرمت ۲ — دو خطی:**
```
دسته: بسکتبال
موضوع: مروری بر فینال NBA امسال
```

اگر دسته‌بندی نگذاری، به‌طور پیش‌فرض «سایر» (ID=6) در نظر گرفته می‌شود.

چند ثانیه بعد، ربات پیام «✅ مقاله منتشر شد + لینک» را برایت می‌فرستد و پست با تصویر کاور در سایت ArioSport ظاهر می‌شود.

---

## ۹) درباره‌ی «متن استاندارد، نه HTML»
طبق خواسته‌ات، **هوش مصنوعی متن مقاله را به صورت متن استاندارد و خوانا می‌نویسد** (بدون تگ HTML و بدون مارک‌داون).

چون فیلد `content` در جنگو از نوع CKEditor (RichText) است، گره **Format Article** فقط یک کار سبک انجام می‌دهد: پاراگراف‌ها را با `<p>` بسته‌بندی می‌کند تا در سایت درست و با فاصله نمایش داده شوند. خود متن دست‌نخورده و استاندارد می‌ماند.

اگر می‌خواهی **کاملاً متن خام** (بدون هیچ `<p>`) ذخیره شود:
- در گره **Create Post (Django)**، مقدار فیلد `content` را از
  `{{ $('Format Article').item.json.content }}`
  به
  `{{ $('Format Article').item.json.rawText }}`
  تغییر بده. (فیلد `rawText` دقیقاً همان متن استاندارد بدون هیچ تگ است.)

---

## ۱۰) چک‌لیست نهایی قبل از اجرا
- [ ] DRF نصب و در `INSTALLED_APPS` اضافه شد
- [ ] فایل `Blog_Module/api.py` ساخته شد
- [ ] مسیرهای `api/posts/create/` و `api/categories/` در `urls.py` اضافه شدند
- [ ] کاربر ادمین (superuser) وجود دارد
- [ ] دسته‌بندی‌ها در دیتابیس پر شده‌اند و ID ها چک شدند
- [ ] سرور جنگو از طریق یک **آدرس عمومی** قابل دسترسی است و در `ALLOWED_HOSTS` ثبت شده
- [ ] سه Credential در n8n ساخته و به گره‌ها وصل شدند
- [ ] URL واقعی در گره Create Post گذاشته شد
- [ ] مدل‌های Gemini انتخاب شدند
- [ ] ورک‌فلو **Active** شد

---

## ۱۱) رفع اشکال (Troubleshooting)
| مشکل | راه‌حل |
|------|--------|
| خطای CSRF | دکوراتور `@csrf_exempt` روی ویوها هست؟ |
| خطای 401/403 | Basic Auth درست است؟ کاربر `is_staff` است؟ `BasicAuthentication` در `REST_FRAMEWORK` فعال است؟ |
| آپلود عکس ناموفق | دسترسی نوشتن روی `MEDIA_ROOT` و درست بودن `cover_image` به‌صورت باینری |
| دسته اشتباه | از `/api/categories/` ID واقعی را بگیر و `categoryMap` را اصلاح کن |
| n8n به سرور وصل نمی‌شود | آدرس عمومی (ngrok/دامنه) درست است؟ در `ALLOWED_HOSTS` هست؟ HTTPS است؟ |
| متن انگلیسی شد | پرامپت گره Write Article تأکید «به فارسی» دارد؛ در صورت نیاز پررنگ‌ترش کن |
| مدل تصویر کار نمی‌کند | در گره Generate Cover Image یک مدل تصویری موجود در حساب Gemini انتخاب کن |
| ربات جواب نمی‌دهد | ورک‌فلو Active است؟ Credential تلگرام درست وصل شده؟ |

---

موفق باشی! 🎉 با هر بار پیام دادن به ربات، یک مقاله‌ی کامل با تصویر کاور به‌صورت خودکار در ArioSport منتشر می‌شود.
