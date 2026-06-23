"""
Django settings for ArioSport sports blog project.
Configured for PythonAnywhere deployment.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-ariosport-local-dev-key-change-in-production-9z3k!x"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "ariosport.pythonanywhere.com"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Third party
    "ckeditor",
    "ckeditor_uploader",
    # Project modules
    "Core_Module",
    "Accounts_Module",
    "Category_Module",
    "Blog_Module",
    "Home_Module",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ArioSport.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                # Project context processors
                "Core_Module.context_processors.site_settings",
                "Category_Module.context_processors.nav_categories",
                "Accounts_Module.context_processors.admin_badges",
            ],
        },
    },
]

WSGI_APPLICATION = "ArioSport.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---- Localization (Persian / RTL) ----
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ---- Static & Media ----
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Auth redirects ----
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "home:index"

# ---- Messages -> bootstrap-like tags (used by template) ----
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: "info",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}

# Email (console backend for local dev)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "ArioSport <no-reply@ariosport.local>"

# ---- CKEditor ----
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_BROWSE_SHOW_DIRS = True
CKEDITOR_ALLOW_NONIMAGE_FILES = False
CKEDITOR_SHOW_WARNING = False

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono-lisa",
        "toolbar": "full",
        "height": 500,
        "width": "100%",
        "language": "fa",
        "directionality": "rtl",
        "allowedContent": False,
        "forcePasteAsPlainText": False,
        "extraPlugins": ",".join([
            "uploadimage",
            "uploadfile",
            "autolink",
            "autoembed",
            "widget",
            "lineutils",
            "clipboard",
            "dialog",
            "dialogui",
        ]),
        "removePlugins": "exportpdf",
        "format_tags": "p;h1;h2;h3;h4;pre;address;div",
        "font_names": "Vazirmatn/Vazirmatn;Manrope/Manrope;Tahoma;Arial;Times New Roman",
        "fontSize_sizes": "12/12px;14/14px;16/16px;18/18px;20/20px;24/24px;28/28px;32/32px;36/36px;48/48px",
        "stylesSet": [
            {"name": "Heading 1", "element": "h1"},
            {"name": "Heading 2", "element": "h2"},
            {"name": "Heading 3", "element": "h3"},
            {"name": "Paragraph", "element": "p"},
            {"name": "Blockquote", "element": "blockquote"},
            {"name": "Code Block", "element": "pre"},
        ],
    },
}

X_FRAME_OPTIONS = "DENY"

# ---- Image upload compression settings ----
IMAGE_UPLOAD_MAX_WIDTH = 1920
IMAGE_UPLOAD_MAX_HEIGHT = 1080
IMAGE_UPLOAD_QUALITY = 82
IMAGE_UPLOAD_MAX_SIZE_MB = 10
