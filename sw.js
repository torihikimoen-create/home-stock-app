/* ──────────────────────────────────────────────────────
   ほめストック — Service Worker
   キャッシュ戦略: Cache First（オフライン対応）
────────────────────────────────────────────────────── */

const CACHE_NAME = 'home-stock-v1';

// キャッシュするリソース
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/app.html',
  '/style.css',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  // Google Fonts はキャッシュ対象外（ネットワーク優先）
];

// ── Install ──────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_URLS).catch(err => {
        // 一部ファイル取得失敗しても続行
        console.warn('[SW] precache partial failure', err);
      });
    })
  );
  self.skipWaiting();
});

// ── Activate ─────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch ────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Google Fonts などの外部リソースはネットワーク優先
  if (url.origin !== location.origin) {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match(request))
    );
    return;
  }

  // 自ドメインリソース: Cache First
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        // 正常なレスポンスのみキャッシュ
        if (response && response.status === 200 && response.type === 'basic') {
          const toCache = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, toCache));
        }
        return response;
      }).catch(() => {
        // オフライン時のフォールバック
        if (request.destination === 'document') {
          return caches.match('/app.html');
        }
      });
    })
  );
});
