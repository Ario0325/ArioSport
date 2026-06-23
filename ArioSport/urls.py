from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from Blog_Module.sitemaps import PostSitemap, StaticSitemap
from Blog_Module.api import create_post_api, list_categories_api, api_health
from Core_Module import views as core_views

sitemaps = {"posts": PostSitemap, "static": StaticSitemap}

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("", include("Home_Module.urls")),
    path("blog/", include("Blog_Module.urls")),
    path("category/", include("Category_Module.urls")),
    path("accounts/", include("Accounts_Module.urls")),
    path("admin/", include("Accounts_Module.admin_urls")),
    path("", include("Core_Module.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    # n8n API endpoints
    path("api/health/", api_health, name="api_health"),
    path("api/posts/create/", create_post_api, name="api_create_post"),
    path("api/categories/", list_categories_api, name="api_categories"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")

handler403 = "Core_Module.views.error_403"
handler404 = "Core_Module.views.error_404"
handler500 = "Core_Module.views.error_500"
