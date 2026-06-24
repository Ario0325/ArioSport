import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError
from django.conf import settings

logger = logging.getLogger(__name__)


def send_auth_event(event, email, username="", code="", reset_link=""):
    webhook_url = getattr(settings, "N8N_WEBHOOK_URL", "")
    secret_token = getattr(settings, "N8N_SECRET_TOKEN", "")
    use_proxy = getattr(settings, "N8N_USE_CLOUDFLARE_PROXY", False)
    proxy_url = getattr(settings, "CLOUDFLARE_WORKER_URL", "")

    if use_proxy and proxy_url:
        target_url = proxy_url.rstrip("/") + "/proxy/n8n/auth-event"
    else:
        target_url = webhook_url

    if not target_url:
        logger.warning("N8N_WEBHOOK_URL is not configured. Skipping email send.")
        return False

    payload = {
        "event": event,
        "email": email,
        "username": username,
        "code": code,
        "reset_link": reset_link,
        "secret_token": secret_token,
        "sender_email": getattr(settings, "N8N_SENDER_EMAIL", ""),
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(target_url, data=data, headers={
            "Content-Type": "application/json",
            "User-Agent": "ArioSport-Django/1.0",
        }, method="POST")
        with urlopen(req, timeout=15) as resp:
            status = resp.status
            logger.info(f"OTP webhook response ({target_url}): {status}")
            return 200 <= status < 300
    except URLError as e:
        logger.error(f"OTP webhook error: {e}")
        return False
    except Exception as e:
        logger.error(f"OTP unexpected error: {e}")
        return False
