/**
 * ArioSport Cloudflare Worker Proxy
 *
 * این Worker به عنوان واسط بین n8n و PythonAnywhere عمل می‌کند.
 * مسیر:
 *   n8n → Cloudflare Worker → PythonAnywhere (Django API)
 *   PythonAnywhere → Cloudflare Worker → n8n (اختیاری)
 *
 * مسیرهای مجاز:
 *   POST /api/posts/create/  → ساخت مقاله جدید
 *   GET  /api/categories/    → لیست دسته‌بندی‌ها
 *   GET  /api/health/        → بررسی سلامت
 */

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // --- CORS preflight ---
    if (request.method === "OPTIONS") {
      return handleCors(new Response(null, { status: 204 }), env);
    }

    // --- Health check (بدون پروکسی) ---
    if (path === "/api/health" || path === "/api/health/") {
      return handleCors(
        JsonResponse({ status: "ok", service: "ArioSport Proxy", timestamp: new Date().toISOString() }),
        env
      );
    }

    // --- بررسی مسیر مجاز ---
    const allowedPaths = (env.ALLOWED_PATHS || "").split(",").map(p => p.trim());
    const isAllowed = allowedPaths.some(ap => path === ap || path === ap.replace(/\/$/, ""));

    if (!isAllowed) {
      return handleCors(
        JsonResponse({ error: "Path not allowed through proxy.", path }, 403),
        env
      );
    }

    // --- ساخت درخواست به PythonAnywhere ---
    const djangoOrigin = env.DJANGO_ORIGIN;
    if (!djangoOrigin) {
      return handleCors(
        JsonResponse({ error: "DJANGO_ORIGIN not configured." }, 500),
        env
      );
    }

    const targetUrl = djangoOrigin + path + url.search;

    // کپی هدرها
    const headers = new Headers();
    for (const [key, value] of request.headers) {
      // هدرهای امنیتی را کپی نکن
      const skipHeaders = ["host", "origin", "referer", "cf-connecting-ip", "cf-ray", "cf-visitor"];
      if (!skipHeaders.includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    }

    // هدر مخصوص Worker تا Django بداند درخواست از پروکسی می‌آید
    headers.set("X-Forwarded-For", request.headers.get("cf-connecting-ip") || "unknown");
    headers.set("X-Proxy-Source", "cloudflare-worker");

    try {
      const proxyRequest = new Request(targetUrl, {
        method: request.method,
        headers: headers,
        body: request.method !== "GET" && request.method !== "HEAD" ? request.body : null,
      });

      const response = await fetch(proxyRequest);
      const responseHeaders = new Headers(response.headers);

      // حذف هدرهایی که نباید به کلاینت برگردند
      responseHeaders.delete("x-frame-options");
      responseHeaders.delete("content-security-policy");

      return handleCors(
        new Response(response.body, {
          status: response.status,
          statusText: response.statusText,
          headers: responseHeaders,
        }),
        env
      );
    } catch (err) {
      return handleCors(
        JsonResponse({ error: "Proxy error", detail: err.message }, 502),
        env
      );
    }
  },
};

/**
 * ساخت JSON response
 */
function JsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

/**
 * اضافه کردن هدرهای CORS
 */
function handleCors(response, env) {
  const newHeaders = new Headers(response.headers);
  // اجازه دسترسی از همه (برای n8n cloud)
  newHeaders.set("Access-Control-Allow-Origin", "*");
  newHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  newHeaders.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
  newHeaders.set("Access-Control-Max-Age", "86400");
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}
