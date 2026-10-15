// v2 (15/10/2026): a v1 guardava respostas da API (dados de saúde) no cache do
// aparelho e mostrava dados velhos. Trocar o nome faz o "activate" abaixo apagar
// o cache antigo em todos os aparelhos assim que esta versão for instalada.
const CACHE_NAME = "nymphia-pwa-v2";
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
// 1. Navegação (HTML): rede primeiro, com a casca do app em cache para funcionar offline (garante /emergencia)
// 2. Arquivos estáticos (JS, CSS, imagens, ícones): cache com revalidação
// 3. TODO o resto passa direto pela rede, sem cache. A API da Nymphia não usa o
//    prefixo /api (são rotas como /checkin, /vinculo, /auth), então antes ela
//    caía na regra de estáticos: o app mostrava a resposta ANTERIOR guardada no
//    aparelho (ex.: painel do médico sem o alerta mais novo) e, num aparelho
//    compartilhado, a pessoa seguinte podia ver os dados da anterior.
const EXTENSOES_ESTATICAS = /\.(?:js|css|png|svg|jpg|jpeg|webp|gif|ico|woff2?|ttf|webmanifest)$/i;

function ehArquivoEstatico(url) {
  return url.origin === self.location.origin &&
    (url.pathname.startsWith("/assets/") || EXTENSOES_ESTATICAS.test(url.pathname));
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== "GET") {
    return;
  }
  if (request.mode !== "navigate" && !ehArquivoEstatico(url)) {
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
