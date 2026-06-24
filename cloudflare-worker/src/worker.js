/**
 * ArioSport Cloudflare Worker Proxy
 *
 * این Worker به عنوان واسط بین n8n و PythonAnywhere عمل می‌کند.
 * مسیرها:
 *   n8n → Cloudflare Worker → PythonAnywhere (Django API)
 *   PythonAnywhere → Cloudflare Worker → n8n (OTP webhook)
 *
 * مسیرهای مجاز:
 *   POST /api/posts/create/        → ساخت مقاله جدید
 *   GET  /api/categories/          → لیست دسته‌بندی‌ها
 *   GET  /api/health/              → بررسی سلامت
 *   POST /proxy/n8n/auth-event     → ارسال OTP به n8n
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

    // --- پروکسی OTP به n8n ---
    if (path === "/proxy/n8n/auth-event" || path === "/proxy/n8n/auth-event/") {
      return proxyToN8n(request, env);
    }

    // --- بررسی مسیر مجاز (پروکسی به Django) ---
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

    const headers = new Headers();
    for (const [key, value] of request.headers) {
      const skipHeaders = ["host", "origin", "referer", "cf-connecting-ip", "cf-ray", "cf-visitor"];
      if (!skipHeaders.includes(key.toLowerCase())) {
        headers.set(key, value);
      }
    }

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
 * پروکسی درخواست OTP از Django به n8n
 */
async function proxyToN8n(request, env) {
  const n8nWebhookUrl = env.N8N_WEBHOOK_URL;
  const secretToken = env.N8N_SECRET_TOKEN;

  if (!n8nWebhookUrl) {
    return handleCors(
      JsonResponse({ error: "N8N_WEBHOOK_URL not configured." }, 500),
      env
    );
  }

  // بررسی توکن امنیتی
  let body;
  try {
    body = await request.json();
  } catch {
    return handleCors(
      JsonResponse({ error: "Invalid JSON body." }, 400),
      env
    );
  }

  if (body.secret_token !== secretToken) {
    return handleCors(
      JsonResponse({ error: "Unauthorized: invalid secret token." }, 401),
      env
    );
  }

  try {
    const n8nResponse = await fetch(n8nWebhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "ArioSport-Worker/1.0",
      },
      body: JSON.stringify(body),
    });

    const responseData = await n8nResponse.text();

    return handleCors(
      new Response(responseData, {
        status: n8nResponse.status,
        headers: { "Content-Type": "application/json; charset=utf-8" },
      }),
      env
    );
  } catch (err) {
    return handleCors(
      JsonResponse({ error: "Failed to reach n8n.", detail: err.message }, 502),
      env
    );
  }
}

function JsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function handleCors(response, env) {
  const newHeaders = new Headers(response.headers);
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
