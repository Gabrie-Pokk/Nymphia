const CACHE_NAME = "nymphia-pwa-v1";
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/lotus-logo.svg",
  "/icon-192.svg",
  "/icon-512.svg"
];

// Instalação: Pré-cache dos ativos estruturais essenciais e da casca do app
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Ativação: Limpeza de caches obsoletos
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Interceptação de requisições:
// 1. Requisições de navegação (HTML): Network-first com fallback para Cache (garante /emergencia offline)
// 2. Requisições estáticas (JS/CSS/Imagens): Cache-first com revalidação
// 3. Chamadas de API (/auth, /checkin, etc): Sempre rede com tratamento gracioso de offline
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Não intercepta chamadas de API ou requisições não-GET
  if (request.method !== "GET" || url.pathname.startsWith("/api") || url.pathname.startsWith("/storage")) {
    return;
  }

  // Navegação para páginas SPA (como /emergencia, /login, /gestante/home)
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        // Fallback offline: entrega a aplicação em cache
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match("/index.html");
        return cachedResponse || new Response(
          "<html><body style='font-family:sans-serif;padding:2rem;text-align:center;background:#FDF0F2;color:#5C1A2A;'>" +
          "<h2>Nymphia Offline</h2><p>Você está sem conexão com a internet.</p>" +
          "<p><strong>Em caso de emergência obstétrica, ligue imediatamente para o SAMU 192.</strong></p>" +
          "</body></html>",
          { headers: { "Content-Type": "text/html; charset=utf-8" } }
        );
      })
    );
    return;
  }

  // Ativos estáticos: Stale-While-Revalidate
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, responseToCache));
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
