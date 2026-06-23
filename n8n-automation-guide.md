# ArioSport Blog — n8n Automation Guide

## 1. Project Overview

**ArioSport** is a Persian (RTL) sports blog built with **Django 4.2+**, **SQLite**, and **CKEditor**.
The goal is to build an n8n workflow that **automatically generates and publishes sports articles** — both text and cover images — using AI.

---

## 2. Database & Models

### 2.1 Category (Category_Module)

| Field         | Type         | Notes                          |
|---------------|--------------|--------------------------------|
| `id`          | AutoField    | PK                             |
| `name`        | Char(80)     | Unique, e.g. "فوتبال"          |
| `slug`        | SlugField    | Auto-generated from name       |
| `description` | Text         | Optional                       |
| `icon`        | Char(40)     | Lucide icon name               |
| `order`       | PositiveInt  | Display order                  |
| `is_active`   | Boolean      | Default True                   |
| `created_at`  | DateTime     | Auto                           |

### 2.2 Tag (Blog_Module)

| Field  | Type      | Notes                    |
|--------|-----------|--------------------------|
| `id`   | AutoField | PK                       |
| `name` | Char(60)  | Unique                   |
| `slug` | SlugField | Auto-generated from name |

### 2.3 Post (Blog_Module)

| Field          | Type             | Notes                                      |
|----------------|------------------|--------------------------------------------|
| `id`           | AutoField        | PK                                         |
| `title`        | Char(220)        | Article title                              |
| `slug`         | SlugField(255)   | Auto-generated from title, unique          |
| `category_id`  | FK → Category    | Required                                   |
| `author_id`    | FK → User        | Can be null                                |
| `excerpt`      | Text(400)        | Short summary for card display             |
| `content`      | RichText         | Full HTML article (CKEditor)               |
| `cover_image`  | ImageField       | Upload to `posts/YYYY/MM/`                 |
| `tags`         | M2M → Tag        | Optional                                   |
| `status`       | Char(10)         | `"draft"` or `"published"`                 |
| `is_featured`  | Boolean          | Default False                              |
| `reading_time` | PositiveInt      | Auto-calculated (~200 wpm)                 |
| `views`        | PositiveInt      | Default 0                                  |
| `published_at` | DateTime         | Auto-set when status = published           |
| `created_at`   | DateTime         | Auto                                       |
| `updated_at`   | DateTime         | Auto                                       |

### 2.4 Comment (Blog_Module)

| Field        | Type         | Notes                     |
|--------------|--------------|---------------------------|
| `id`         | AutoField    | PK                        |
| `post_id`    | FK → Post    | Required                  |
| `user_id`    | FK → User    | Optional                  |
| `parent_id`  | FK → Comment | Optional (for replies)    |
| `name`       | Char(120)    | Commenter name            |
| `email`      | Email        | Optional                  |
| `body`       | Text         | Comment text              |
| `is_approved`| Boolean      | Default False             |
| `created_at` | DateTime     | Auto                      |

---

## 3. Django Admin API for n8n

Django does **not** expose a REST API by default. You have two options:

### Option A: Django REST Framework (Recommended)

Install DRF and create endpoints:

```
pip install djangorestframework
```

Create `Blog_Module/api.py`:

```python
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Post, Tag
from Category_Module.models import Category


class IsAdminOrPostOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return True
        return request.user and request.user.is_staff


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def create_post_api(request):
    """
    Create a new blog post via API.
    Accepts multipart/form-data for image upload.
    
    Required fields:
      - title: str
      - category_id: int
      - content: str (HTML)
    
    Optional fields:
      - excerpt: str
      - cover_image: file
      - tags: comma-separated tag names
      - status: "draft" or "published"
      - is_featured: bool
      - author_id: int
    """
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
        is_featured=data.get("is_featured", False),
    )

    author_id = data.get("author_id")
    if author_id:
        from django.contrib.auth.models import User
        try:
            post.author = User.objects.get(id=author_id)
        except User.DoesNotExist:
            pass

    if "cover_image" in request.FILES:
        post.cover_image = request.FILES["cover_image"]

    post.save()

    # Handle tags (comma-separated names)
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


@api_view(["GET"])
@permission_classes([permissions.IsAdminUser])
def list_categories_api(request):
    """List all active categories with their IDs."""
    cats = Category.objects.filter(is_active=True).values("id", "name", "slug")
    return Response(list(cats))
```

Add to `ArioSport/urls.py`:

```python
from Blog_Module.api import create_post_api, list_categories_api

urlpatterns = [
    # ... existing patterns ...
    path("api/posts/create/", create_post_api, name="api_create_post"),
    path("api/categories/", list_categories_api, name="api_categories"),
]
```

### Option B: Direct SQLite Access

n8n can connect to SQLite directly using the **Execute Command** node or a custom script.
Database file: `db.sqlite3`

---

## 4. n8n Workflow Design

### 4.1 Workflow: Auto-Generate & Publish Article

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Trigger     │───▶│  AI: Topic   │───▶│  AI: Article │───▶│  AI: Image   │
│  (Schedule/  │    │  Generator   │    │  Writer      │    │  Generator   │
│   Manual)    │    │              │    │              │    │              │
└─────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                  │
                                                                  ▼
                           ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
                           │  Django API  │◀───│  Format Data │◀───│  Download    │
                           │  Create Post │    │  for Django  │    │  Image       │
                           └──────────────┘    └──────────────┘    └──────────────┘
```

### 4.2 Step-by-Step Node Configuration

#### Step 1: Trigger Node

**Type:** Schedule Trigger or Manual Trigger

- **Schedule:** e.g., every day at 8:00 AM Tehran time
- **Manual:** For on-demand generation

#### Step 2: AI — Topic & Title Generator

**Type:** OpenAI / HTTP Request (to any LLM API)

**System Prompt:**
```
تو یک نویسنده حرفه‌ای مقالات ورزشی فارسی هستی برای وبلاگ ArioSport.
یک موضوع جذاب و مرتبط با ورزش انتخاب کن.

خروجی JSON:
{
  "title": "عنوان مقاله به فارسی",
  "category_suggestion": "نام دسته‌بندی پیشنهادی",
  "tags": ["برچسب۱", "برچسب۲", "برچسب۳"],
  "excerpt": "خلاصه ۲-۳ جمله‌ای مقاله"
}

موضوعات محبوب: فوتبال، بسکتبال، والیبال، تنیس، MMA، فرمول یک، لیگ برتر ایران، لیگ قهرمانان اروپا، NBA
```

**Output:** JSON with title, category, tags, excerpt

#### Step 3: AI — Article Writer

**Type:** OpenAI / HTTP Request

**System Prompt:**
```
تو یک نویسنده حرفه‌ای مقالات ورزشی فارسی هستی برای وبلاگ ArioSport.
مقاله‌ای کامل و جذاب بنویس با این مشخصات:

عنوان: {{$json.title}}
موضوع: {{$json.excerpt}}

قوانین:
1. متن به فارسی باشد
2. حداقل ۸۰۰ کلمه
3. از تگ‌های HTML استفاده کن (h2, h3, p, ul, li, blockquote, strong)
4. ساختار: مقدمه، بدنه اصلی (۳-۴ بخش با عنوان)، نتیجه‌گیری
5. لحن حرفه‌ای اما صمیمی
6. آمار و ارقام واقعی در صورت امکان
7. محتوای CKEditor سازگار باشد

خروجی فقط HTML مقاله (بدون تگ‌های html/head/body).
```

**Output:** Full HTML article content

#### Step 4: AI — Image Generator

**Type:** HTTP Request to DALL-E / Midjourney API / Stable Diffusion

**Prompt Construction:**
```
A professional sports blog cover image for an article titled: {{$json.title}}
Style: modern, clean, editorial, suitable for a Persian sports website.
Aspect ratio: 16:9, high quality, no text overlay.
```

**API Options:**
- **OpenAI DALL-E 3:** `POST https://api.openai.com/v1/images/generations`
- **Stability AI:** `POST https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image`
- **Replicate:** Various models available

#### Step 5: Download Generated Image

**Type:** HTTP Request

Download the image from the URL returned by the image generation API.

**Settings:**
- Response Format: File
- Output: Binary data

#### Step 6: Format Data for Django

**Type:** Code Node (JavaScript)

```javascript
// Combine all AI outputs into Django-compatible format
const title = $('Topic Generator').first().json.title;
const excerpt = $('Topic Generator').first().json.excerpt;
const content = $('Article Writer').first().json.choices[0].message.content;
const tags = $('Topic Generator').first().json.tags.join(',');
const categorySuggestion = $('Topic Generator').first().json.category_suggestion;

// You need to map category name to ID
// Option 1: Hardcode known categories
const categoryMap = {
  'فوتبال': 1,
  'بسکتبال': 2,
  'والیبال': 3,
  'تنیس': 4,
  'ورزش‌های رزمی': 5,
  'سایر': 6,
};

const categoryId = categoryMap[categorySuggestion] || 1;

return [{
  json: {
    title,
    excerpt,
    content,
    tags,
    category_id: categoryId,
    status: 'published',
    is_featured: false,
  }
}];
```

#### Step 7: Create Post via Django API

**Type:** HTTP Request

**Settings:**
- **Method:** POST
- **URL:** `https://your-domain.com/api/posts/create/`
- **Authentication:** Basic Auth (admin credentials) or Token Auth
- **Body:** Multipart Form Data
  - `title`: `{{$json.title}}`
  - `category_id`: `{{$json.category_id}}`
  - `content`: `{{$json.content}}`
  - `excerpt`: `{{$json.excerpt}}`
  - `tags`: `{{$json.tags}}`
  - `status`: `{{$json.status}}`
  - `cover_image`: Binary file from Step 5

---

## 5. Category Reference

| ID | Name (Persian)    | Slug           | Icon        |
|----|-------------------|----------------|-------------|
| 1  | فوتبال            | football       | goal        |
| 2  | بسکتبال           | basketball     | dribbble    |
| 3  | والیبال           | volleyball     | circle-dot  |
| 4  | تنیس              | tennis         | racket      |
| 5  | ورزش‌های رزمی     | martial-arts   | swords      |
| 6  | سایر              | other          | layout-grid |

> **Note:** Check actual category IDs in your database. Use the `/api/categories/` endpoint to get real IDs.

---

## 6. Environment Variables for n8n

Set these in n8n credentials or environment:

```
DJANGO_API_URL=https://your-domain.com
DJANGO_ADMIN_USER=your-admin-username
DJANGO_ADMIN_PASS=your-admin-password
OPENAI_API_KEY=sk-...
IMAGE_API_KEY=sk-...  # DALL-E / Stability AI / etc.
```

---

## 7. Advanced Workflow Ideas

### 7.1 RSS-Based Topic Discovery
```
RSS Feed (sports news) → Filter duplicates → AI Rewrite → Publish
```

### 7.2 Image Prompt Enhancement
```
Topic → AI generates detailed image prompt → Image API → Better results
```

### 7.3 SEO Optimization
```
Article → AI adds meta description, internal links, related tags → Publish
```

### 7.4 Social Media Cross-Post
```
Post Published → Generate Instagram caption → Post to Instagram/Telegram
```

### 7.5 Content Calendar
```
Google Sheet (content plan) → Read next topic → Generate → Schedule publish
```

---

## 8. Django Setup Checklist

Before running n8n automation, ensure:

- [ ] Django server is running and accessible
- [ ] Admin user exists with API permissions
- [ ] API endpoints are created (see Section 3)
- [ ] Categories are populated in database
- [ ] `ALLOWED_HOSTS` includes n8n server IP
- [ ] CORS headers configured if needed (`django-cors-headers`)
- [ ] Media upload directory is writable
- [ ] CSRF exempt for API views (or use token auth)

### CSRF Exemption for API

Add to `Blog_Module/api.py`:

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def create_post_api(request):
    # ... same as above
```

---

## 9. Sample n8n Workflow JSON

```json
{
  "name": "ArioSport Auto Blog",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{ "field": "cronExpression", "expression": "0 8 * * *" }]
        }
      }
    },
    {
      "name": "Generate Topic",
      "type": "n8n-nodes-base.openAi",
      "parameters": {
        "resource": "chat",
        "model": "gpt-4o",
        "messages": {
          "values": [
            { "role": "system", "content": "تو یک نویسنده حرفه‌ای ورزشی فارسی هستی. یک موضوع جذاب ورزشی پیشنهاد بده. خروجی JSON: {\"title\": \"...\", \"category_suggestion\": \"...\", \"tags\": [...], \"excerpt\": \"...\"}" },
            { "role": "user", "content": "یک مقاله ورزشی جدید پیشنهاد بده." }
          ]
        }
      }
    },
    {
      "name": "Write Article",
      "type": "n8n-nodes-base.openAi",
      "parameters": {
        "resource": "chat",
        "model": "gpt-4o",
        "messages": {
          "values": [
            { "role": "system", "content": "مقاله ورزشی فارسی کامل بنویس. حداقل ۸۰۰ کلمه. از HTML تگ‌های h2,h3,p,ul,li,blockquote,strong استفاده کن. فقط HTML خروجی بده." },
            { "role": "user", "content": "عنوان: {{$json.title}}\nموضوع: {{$json.excerpt}}" }
          ]
        }
      }
    },
    {
      "name": "Generate Image",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://api.openai.com/v1/images/generations",
        "authentication": "genericCredentialType",
        "sendBody": true,
        "bodyParameters": {
          "model": "dall-e-3",
          "prompt": "Professional sports blog cover: {{$json.title}}. Modern, clean, editorial style.",
          "n": 1,
          "size": "1792x1024"
        }
      }
    },
    {
      "name": "Create Post",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "={{$env.DJANGO_API_URL}}/api/posts/create/",
        "authentication": "genericCredentialType",
        "sendBody": true,
        "contentType": "multipart-form-data"
      }
    }
  ],
  "connections": {
    "Schedule": { "main": [[{ "node": "Generate Topic", "type": "main", "index": 0 }]] },
    "Generate Topic": { "main": [[{ "node": "Write Article", "type": "main", "index": 0 }]] },
    "Write Article": { "main": [[{ "node": "Generate Image", "type": "main", "index": 0 }]] },
    "Generate Image": { "main": [[{ "node": "Create Post", "type": "main", "index": 0 }]] }
  }
}
```

---

## 10. Troubleshooting

| Issue | Solution |
|-------|----------|
| CSRF error on API | Add `@csrf_exempt` decorator |
| Image upload fails | Check `MEDIA_ROOT` permissions |
| Wrong category ID | Call `/api/categories/` to get real IDs |
| Duplicate slugs | Django auto-appends `-1`, `-2`, etc. |
| Content too short | Increase min word count in AI prompt |
| AI generates English | Add explicit "به فارسی" instruction |
| Image generation timeout | Increase n8n timeout or use async workflow |

---

## 11. File Structure Summary

```
ArioSport_Blog/
├── ArioSport/          # Django project settings
│   ├── settings.py     # Database, media, CKEditor config
│   └── urls.py         # URL routing (add API endpoints here)
├── Blog_Module/        # Blog app
│   ├── models.py       # Post, Tag, Comment models
│   ├── api.py          # ← CREATE THIS for n8n API
│   └── admin.py        # Admin configuration
├── Category_Module/    # Category app
│   └── models.py       # Category model
├── Core_Module/        # Site settings, utils
│   └── utils.py        # Image compression
├── Accounts_Module/    # User profiles
├── media/              # Uploaded files (images)
├── db.sqlite3          # SQLite database
└── requirements.txt    # Django, Pillow, CKEditor
```
