"""
تست کامل سیستم OTP آریو اسپورت
اجرا: python test_otp_system.py
"""
import os
import sys
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("otp-test")

TEST_EMAIL = "Bardiaabdi1393@gmail.com"
TEST_CODE = "654321"
TEST_USERNAME = "کاربر تست"

WORKER_URL = "https://ariosport-proxy.mimoomim456.workers.dev"
N8N_WEBHOOK_URL = "https://ariosport.app.n8n.cloud/webhook/django-auth-event"
SECRET_TOKEN = "ario-shop-secret-token"
SENDER_EMAIL = "codeclaude080@gmail.com"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "ArioSport-Django/1.0",
}


def test_worker_health():
    log.info("=" * 50)
    log.info("تست ۱: سلامت Cloudflare Worker")
    log.info("=" * 50)
    url = f"{WORKER_URL}/api/health"
    log.info(f"URL: {url}")
    try:
        req = Request(url, method="GET")
        req.add_header("User-Agent", "ArioSport-Django/1.0")
        with urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
            log.info(f"Status: {resp.status}")
            log.info(f"Response: {data}")
            if resp.status == 200:
                log.info("✅ Cloudflare Worker فعال است")
                return True
            else:
                log.error("❌ Cloudflare Worker پاسخ غیرمنتظره داد")
                return False
    except URLError as e:
        log.error(f"❌ خطا در اتصال به Cloudflare Worker: {e}")
        return False
    except Exception as e:
        log.error(f"❌ خطای غیرمنتظره: {e}")
        return False


def test_worker_proxy_to_n8n():
    log.info("")
    log.info("=" * 50)
    log.info("تست ۲: پروکسی Worker به n8n")
    log.info("=" * 50)
    url = f"{WORKER_URL}/proxy/n8n/auth-event"
    payload = {
        "event": "register",
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "code": TEST_CODE,
        "secret_token": SECRET_TOKEN,
        "sender_email": SENDER_EMAIL,
    }
    log.info(f"URL: {url}")
    log.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers=HEADERS, method="POST")
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            log.info(f"Status: {resp.status}")
            log.info(f"Response: {body}")
            if resp.status == 200:
                log.info("✅ ایمیل OTP با موفقیت ارسال شد")
                log.info(f"📧 کد {TEST_CODE} به {TEST_EMAIL} ارسال شد")
                return True
            else:
                log.warning(f"⚠️ پاسخ غیرمنتظره: {resp.status}")
                return False
    except URLError as e:
        log.error(f"❌ خطا: {e}")
        if hasattr(e, "read"):
            try:
                error_body = e.read().decode()
                log.error(f"Error body: {error_body}")
            except:
                pass
        return False
    except Exception as e:
        log.error(f"❌ خطای غیرمنتظره: {e}")
        return False


def test_direct_n8n():
    log.info("")
    log.info("=" * 50)
    log.info("تست ۳: اتصال مستقیم به n8n (بدون Worker)")
    log.info("=" * 50)
    url = N8N_WEBHOOK_URL
    payload = {
        "event": "register",
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "code": TEST_CODE,
        "secret_token": SECRET_TOKEN,
        "sender_email": SENDER_EMAIL,
    }
    log.info(f"URL: {url}")
    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers=HEADERS, method="POST")
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            log.info(f"Status: {resp.status}")
            log.info(f"Response: {body}")
            if resp.status == 200:
                log.info("✅ اتصال مستقیم به n8n موفق")
                return True
            else:
                log.warning(f"⚠️ پاسخ غیرمنتظره")
                return False
    except URLError as e:
        log.error(f"❌ خطا (PythonAnywhere اتصال مستقیم را بلاک می‌کند - طبیعی است): {e}")
        return False
    except Exception as e:
        log.error(f"❌ خطای غیرمنتظره: {e}")
        return False


def test_password_reset_email():
    log.info("")
    log.info("=" * 50)
    log.info("تست ۴: ارسال ایمیل بازیابی رمز عبور")
    log.info("=" * 50)
    url = f"{WORKER_URL}/proxy/n8n/auth-event"
    payload = {
        "event": "password_reset",
        "email": TEST_EMAIL,
        "username": TEST_USERNAME,
        "code": "987654",
        "secret_token": SECRET_TOKEN,
        "sender_email": SENDER_EMAIL,
    }
    log.info(f"URL: {url}")
    log.info(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers=HEADERS, method="POST")
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode()
            log.info(f"Status: {resp.status}")
            log.info(f"Response: {body}")
            if resp.status == 200:
                log.info("✅ ایمیل بازیابی رمز با موفقیت ارسال شد")
                log.info(f"📧 کد 987654 به {TEST_EMAIL} ارسال شد")
                return True
            else:
                log.warning(f"⚠️ پاسخ غیرمنتظره")
                return False
    except URLError as e:
        log.error(f"❌ خطا: {e}")
        if hasattr(e, "read"):
            try:
                error_body = e.read().decode()
                log.error(f"Error body: {error_body}")
            except:
                pass
        return False
    except Exception as e:
        log.error(f"❌ خطای غیرمنتظره: {e}")
        return False


def main():
    log.info("🚀 شروع تست سیستم OTP آریو اسپورت")
    log.info(f"📧 ایمیل تست: {TEST_EMAIL}")
    log.info(f"🔗 Worker URL: {WORKER_URL}")
    log.info(f"🔗 n8n URL: {N8N_WEBHOOK_URL}")
    log.info("")

    results = {}

    results["worker_health"] = test_worker_health()
    results["worker_proxy"] = test_worker_proxy_to_n8n()
    results["direct_n8n"] = test_direct_n8n()
    results["password_reset"] = test_password_reset_email()

    log.info("")
    log.info("=" * 50)
    log.info("📊 نتایج تست")
    log.info("=" * 50)

    for name, status in results.items():
        icon = "✅" if status else "❌"
        labels = {
            "worker_health": "سلامت Cloudflare Worker",
            "worker_proxy": "پروکسی OTP به n8n",
            "direct_n8n": "اتصال مستقیم به n8n",
            "password_reset": "ایمیل بازیابی رمز",
        }
        log.info(f"{icon} {labels.get(name, name)}: {'موفق' if status else 'ناموفق'}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    log.info("")
    log.info(f"نتیجه: {passed}/{total} تست موفق")

    if results["worker_proxy"]:
        log.info("")
        log.info("🎉 سیستم آماده است!")
        log.info(f"📧 ایمیل‌های تست به {TEST_EMAIL} ارسال شدند")
        log.info("inbox و spam خود را چک کنید")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
