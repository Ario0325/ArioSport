# راهنمای کامل راه‌اندازی Cloudflare Worker + n8n + PythonAnywhere برای ArioSport

## معماری سیستم

```
┌─────────┐      ┌──────────────────────┐      ┌─────────────────────┐
│  n8n    │─────▶│  Cloudflare Worker   │─────▶│  PythonAnywhere     │
│  Cloud  │◀─────│  (Proxy / Bridge)    │◀─────│  (Django + SQLite)  │
└─────────┘      └──────────────────────┘      └─────────────────────┘
  ariosport.app       ariosport-proxy.             ariosport.
  .n8n.cloud          workers.dev                  pythonanywhere.com
```

**چرا Cloudflare Worker لازم است؟**

PythonAnywhere (پلن رایگان) محدودیت‌هایی دارد:
- دسترسی خروجی فقط به سایت‌های لیست‌شده (whitelist)
- نمی‌تواند مستقیماً از n8n درخواست دریافت کند
- نیاز به یک واسط قابل اعتماد برای ارتباط دوطرفه

Cloudflare Worker رایگان است و روزانه **100,000 درخواست** را پشتیبانی می‌کند.

---

## بخش ۱: تنظیمات Django روی PythonAnywhere

### ۱.۱ نصب Django REST Framework (اختیاری — ما از raw view استفاده می‌کنیم)

ما در این پروژه از Django raw views استفاده می‌کنیم (بدون نیاز به DRF).
فقط مطمئن شو فایل `Blog_Module/api.py` وجود دارد.

### ۱.۲ فایل‌های جدید / تغییر یافته

این فایل‌ها باید در پروژه باشند:

| فایل | وضعیت |
|------|-------|
| `Blog_Module/api.py` | ✅ ساخته شد |
| `ArioSport/urls.py` | ✅ آپدیت شد (مسیرهای API اضافه شد) |

### ۱.۳ آپلود روی PythonAnywhere

بعد از push به GitHub:
```bash
# در Bash کنسول PythonAnywhere:
cd ~
git clone https://github.com/USERNAME/ArioSport_Blog.git
# یا اگر قبلاً کلون کردی:
cd ArioSport_Blog
git pull

# نصب dependencies:
pip install --user -r requirements.txt

# مایگریشن:
python manage.py migrate

# مطمئن شو ادمین وجود دارد:
python manage.py createsuperuser

# ری‌لود وب‌اپ (از تب Web روی PythonAnywhere)
```

### ۱.۴ بررسی API روی PythonAnywhere

بعد از ری‌لود، این آدرس‌ها باید کار کنند:

```
GET  https://ariosport.pythonanywhere.com/api/health/
GET  https://ariosport.pythonanywhere.com/api/categories/
POST https://ariosport.pythonanywhere.com/api/posts/create/
```

> **نام کاربری PythonAnywhere خودت** را جایگزین `ariosport` کن.

---

## بخش ۲: ساخت Cloudflare Worker

### ۲.۱ پیش‌نیازها

1. یک حساب **Cloudflare** رایگان: https://dash.cloudflare.com/sign-up
2. **Node.js** نصب شده روی کامپیوتر (نسخه 18+)
3. **Wrangler** (CLI کلادفلر):

```bash
npm install -g wrangler
```

### ۲.۲ لاگین به Cloudflare

```bash
wrangler login
```

مرورگر باز می‌شود → لاگین کن → اجازه بده.

### ۲.۳ ساخت پروژه Worker

```bash
# برو به پوشه cloudflare-worker پروژه:
cd C:\Users\Ario\Downloads\ArioSport_Blog\ArioSport_Blog\cloudflare-worker

# یا اگر می‌خواهی از صفر بسازی:
npm create cloudflare@latest ariosport-proxy -- --type hello-world
cd ariosport-proxy
```

### ۲.۴ فایل‌های پروژه

فایل‌هایی که من ساختم در پوشه `cloudflare-worker/` هستند:

```
cloudflare-worker/
├── wrangler.toml      ← تنظیمات Worker
└── src/
    └── worker.js      ← کد اصلی Worker
```

**wrangler.toml:**
```toml
name = "ariosport-proxy"
main = "src/worker.js"
compatibility_date = "2024-12-01"

[vars]
DJANGO_ORIGIN = "https://ariosport.pythonanywhere.com"
ALLOWED_PATHS = "/api/posts/create/,/api/categories/,/api/health/"
```

> `DJANGO_ORIGIN` را با آدرس واقعی PythonAnywhere خودت عوض کن.

### ۲.۵ تست محلی

```bash
cd cloudflare-worker
npx wrangler dev
```

در مرورگر باز کن: `http://localhost:8787/api/health/`

باید ببینی:
```json
{
  "status": "ok",
  "service": "ArioSport Proxy",
  "timestamp": "2026-06-23T..."
}
```

### ۲.۶ دیپلوی روی Cloudflare

```bash
npx wrangler deploy
```

خروجی چیزی مثل این است:
```
Published ariosport-proxy (X sec)
  https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev
```

**این آدرس را یادداشت کن** — آدرس Worker توست.

### ۲.۷ تست Worker روی Cloudflare

```bash
# Health check:
curl https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev/api/health/

# لیست دسته‌بندی‌ها (با لاگین ادمین):
curl -u "admin:password" https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev/api/categories/
```

---

## بخش ۳: تنظیم n8n برای استفاده از Worker

### ۳.۱ تغییر URL در ورک‌فلو

در ورک‌فلو n8n، گره **Create Post (Django)** را باز کن و URL را تغییر بده:

**قبل (مستقیم به PythonAnywhere — کار نمی‌کند):**
```
https://ariosport.pythonanywhere.com/api/posts/create/
```

**بعد (از طریق Cloudflare Worker):**
```
https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev/api/posts/create/
```

### ۳.۲ تنظیم Credential

در n8n → Credentials → Django Admin Basic Auth:
- **User:** نام کاربری ادمین جنگو
- **Password:** رمز ادمین جنگو

### ۳.۳ تست اتصال

در n8n، یک گره HTTP Request موقت بساز:
- **Method:** GET
- **URL:** `https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev/api/health/`
- **Authentication:** None

اگر جواب گرفتی، اتصال برقرار است.

---

## بخش ۴: امنیت

### ۴.۱ محدود کردن مسیرها

در `wrangler.toml`، فقط مسیرهای مجاز را تعریف کن:
```toml
ALLOWED_PATHS = "/api/posts/create/,/api/categories/,/api/health/"
```

هر مسیر دیگری 403 برمی‌گرداند.

### ۴.۲ محدود کردن Origin (اختیاری)

اگر می‌خواهی فقط n8n بتواند به Worker وصل شود، در `worker.js`:
```javascript
// به جای:
newHeaders.set("Access-Control-Allow-Origin", "*");

// بنویس:
const allowedOrigins = ["https://ariosport.app.n8n.cloud"];
const origin = request.headers.get("Origin");
if (allowedOrigins.includes(origin)) {
  newHeaders.set("Access-Control-Allow-Origin", origin);
}
```

### ۴.۳ Rate Limiting (اختیاری)

Cloudflare رایگان شامل WAF و rate limiting نیست، ولی می‌توانی در Worker ساده‌اش کنی:

```javascript
// ذخیره تعداد درخواست در KV (نیاز به KV namespace دارد)
// یا ساده‌تر: فقط با ALLOWED_PATHS محدودش کن
```

---

## بخش ۵: آدرس‌های مهم

| سرویس | آدرس | توضیح |
|--------|-------|-------|
| **PythonAnywhere** | `https://ariosport.pythonanywhere.com` | سایت اصلی |
| **Django Admin** | `https://ariosport.pythonanywhere.com/django-admin/` | پنل مدیریت |
| **Cloudflare Worker** | `https://ariosport-proxy.SUBDOMAIN.workers.dev` | پروکسی |
| **n8n Cloud** | `https://ariosport.app.n8n.cloud` | اتوماسیون |
| **n8n Workflow** | `https://ariosport.app.n8n.cloud/workflow/x5QX742XSB97nyiw` | ورک‌فلو |

---

## بخش ۶: عیب‌یابی

| مشکل | راه‌حل |
|------|--------|
| Worker 502 می‌دهد | آدرس `DJANGO_ORIGIN` درست است؟ سایت بالاست؟ |
| Worker 403 می‌دهد | مسیر در `ALLOWED_HOSTS` هست؟ |
| Django 401 می‌دهد | Basic Auth درست است؟ کاربر `is_staff` است؟ |
| CORS error | هدرهای CORS در Worker تنظیم شده؟ |
| n8n timeout | PythonAnywhere کند است — timeout را زیاد کن (30s) |
| عکس آپلود نمی‌شود | فایل باینری درست ارسال شده؟ `multipart/form-data`؟ |
| PythonAnywhere sleeping | پلن رایگان بعد از 3 بی‌فعالیتی می‌خوابد — اولین درخواست 30s طول می‌کشد |

### بیدار کردن PythonAnywhere

اگر سایت خوابیده (sleeping)، اول یک درخواست ساده بفرست:
```bash
curl https://ariosport.pythonanywhere.com/api/health/
```
صبر کن تا بیدار شود (تا 30 ثانیه)، بعد درخواست اصلی را بفرست.

---

## بخش ۷: آپدیت Worker

وقتی کد Worker را تغییر دادی:
```bash
cd cloudflare-worker
npx wrangler deploy
```

فوراً اعمال می‌شود (بدون downtime).

---

## بخش ۸: هزینه‌ها

| سرویس | پلن | هزینه |
|--------|------|-------|
| Cloudflare Worker | Free | رایگان (100K req/day) |
| PythonAnywhere | Free | رایگان (محدود) |
| n8n Cloud | Starter | ~20$/ماه یا self-host رایگان |
| Telegram Bot | Free | رایگان |
| Google Gemini | Free tier | رایگان (محدودیت روزانه) |

---

## چک‌لیست نهایی

- [ ] `Blog_Module/api.py` در پروژه هست
- [ ] مسیرهای API در `urls.py` اضافه شده
- [ ] پروژه روی PythonAnywhere آپلود و ری‌لود شده
- [ ] `/api/health/` روی PythonAnywhere کار می‌کند
- [ ] `wrangler login` انجام شده
- [ ] `DJANGO_ORIGIN` در `wrangler.toml` درست تنظیم شده
- [ ] `npx wrangler deploy` انجام شده
- [ ] آدرس Worker یادداشت شده
- [ ] URL گره Create Post در n8n به آدرس Worker تغییر کرده
- [ ] Credential های n8n تنظیم شده
- [ ] تست end-to-end: پیام تلگرام → مقاله منتشر شده
