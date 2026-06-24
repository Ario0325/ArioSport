# راهنمای ستاپ سیستم OTP آریو اسپورت

## خلاصه
سیستم تایید ایمیل با کد OTP برای ثبت‌نام و تغییر رمز عبور پیاده‌سازی شده است.

**مسیر ارتباطی:**
```
Django (PythonAnywhere) → Cloudflare Worker → n8n → Gmail
```

---

## ۱. تنظیمات n8n

### وارد کردن ورک‌فلو
1. فایل `n8n/django-auth-workflow.json` را در n8n ایمپورت کنید
2. روی workflow کلیک کنید و **Import from File** بزنید

### تنظیم Gmail credentials
1. در n8n به بخش **Credentials** بروید
2. یک credential از نوع **Gmail** یا **SMTP** بسازید
3. ایمیل فرستنده: `codeclaude080@gmail.com`
4. اگر از Gmail استفاده می‌کنید، یک **App Password** بسازید:
   - به Google Account → Security → 2-Step Verification → App passwords بروید
   - یک رمز برنامه بسازید و در credential وارد کنید

### فعال‌سازی ورک‌فلو
1. در ورک‌فلو، روی **Send Verification Email** کلیک کنید
2. credential ایمیلی که ساختید را انتخاب کنید
3. همین کار را برای **Send Password Reset Email** تکرار کنید
4. ورک‌فلو را **Active** کنید

---

## ۲. تنظیمات Cloudflare Worker

### نصب Wrangler
```bash
npm install -g wrangler
wrangler login
```

### دیپلوی ورکر
```bash
cd cloudflare-worker
wrangler deploy
```

### تنظیم متغیرهای محیطی
بعد از دیپلوی، در داشبورد Cloudflare → Workers → ariosport-proxy → Settings → Variables:

| متغیر | مقدار |
|---|---|
| `DJANGO_ORIGIN` | `https://ariosport.pythonanywhere.com` |
| `N8N_WEBHOOK_URL` | `https://ariosport.app.n8n.cloud/webhook/django-auth-event` |
| `N8N_SECRET_TOKEN` | `ario-shop-secret-token` |
| `ALLOWED_PATHS` | `/api/posts/create/,/api/categories/,/api/health/` |

آدرس ورکر شما چیزی مثل این خواهد بود:
`https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev`

---

## ۳. تنظیمات Django

### فایل `ArioSport/settings.py`
مقادیر زیر را تنظیم کنید:

```python
# ---- n8n OTP Webhook ----
N8N_WEBHOOK_URL = "https://ariosport.app.n8n.cloud/webhook/django-auth-event"
N8N_SECRET_TOKEN = "ario-shop-secret-token"
N8N_SENDER_EMAIL = "codeclaude080@gmail.com"

# Cloudflare Worker Proxy (برای دور زدن محدودیت PythonAnywhere)
N8N_USE_CLOUDFLARE_PROXY = True
CLOUDFLARE_WORKER_URL = "https://ariosport-proxy.YOUR-SUBDOMAIN.workers.dev"

# OTP Settings
OTP_EXPIRY_MINUTES = 15
```

**نکته:** `CLOUDFLARE_WORKER_URL` را با آدرس ورکر خودتان جایگزین کنید.

---

## ۴. اجرای Migrations

```bash
python manage.py makemigrations Accounts_Module
python manage.py migrate
```

---

## ۵. نحوه کار سیستم

### ثبت‌نام
1. کاربر فرم ثبت‌نام را پر می‌کند
2. حساب کاربری به صورت `is_active=False` ساخته می‌شود
3. کد OTP ۶ رقمی تولید می‌شود
4. Django → Cloudflare Worker → n8n → ایمیل ارسال می‌شود
5. کاربر به صفحه تایید OTP هدایت می‌شود
6. با وارد کردن کد صحیح، حساب فعال شده و کاربر وارد می‌شود

### تغییر رمز عبور
1. کاربر از داشبورد روی «تغییر رمز عبور» کلیک می‌کند
2. صفحه‌ای نمایش داده می‌شود که دکمه «ارسال کد تایید» دارد
3. کد OTP به ایمیل کاربر ارسال می‌شود
4. کاربر کد را وارد می‌کند
5. پس از تایید، فرم تغییر رمز عبور نمایش داده می‌شود

### ارسال مجدد کد
- در صفحه تایید OTP، دکمه «ارسال مجدد کد» با تایمر ۲ دقیقه‌ای وجود دارد
- کدهای قبلی استفاده‌نشده غیرفعال می‌شوند

---

## ۶. فایل‌های ایجاد/تغییر یافته

| فایل | توضیح |
|---|---|
| `Accounts_Module/models.py` | مدل `EmailOTP` اضافه شد |
| `Accounts_Module/views.py` | ویوهای `verify_otp`، `resend_otp` و تغییر `register_view` و `change_password` |
| `Accounts_Module/forms.py` | فرم‌های `OTPVerificationForm` و `PasswordChangeRequestForm` |
| `Accounts_Module/urls.py` | مسیرهای `verify-otp/` و `resend-otp/` |
| `Accounts_Module/n8n_utils.py` | ابزار ارسال وب‌هوک به n8n (با پشتیبانی از پروکسی) |
| `Accounts_Module/admin.py` | ثبت `EmailOTP` در پنل ادمین |
| `ArioSport/settings.py` | تنظیمات n8n، OTP و Cloudflare Worker |
| `static/assets/css/style.css` | استایل‌های OTP |
| `Django n8n (4).json` | اصلاح ایمیل بازیابی رمز (OTP به جای لینک) |
| `cloudflare-worker/src/worker.js` | مسیر پروکسی OTP اضافه شد |
| `cloudflare-worker/wrangler.toml` | متغیرهای n8n اضافه شد |

### تمپلیت‌های جدید
| فایل | توضیح |
|---|---|
| `Accounts_Module/templates/Accounts_Module/verify_otp.html` | صفحه ورود کد OTP |
| `Accounts_Module/templates/Accounts_Module/change_password_request.html` | صفحه درخواست کد برای تغییر رمز |

---

## ۷. تست

### تست محلی
```python
# در settings.py برای تست بدون پروکسی:
N8N_USE_CLOUDFLARE_PROXY = False
```

### بررسی لاگ‌ها
- لاگ‌های Django: `python manage.py runserver`
- لاگ‌های Cloudflare Worker: داشبورد Cloudflare → Workers → Logs
- لاگ‌های n8n: در داشبورد n8n بخش Executions
