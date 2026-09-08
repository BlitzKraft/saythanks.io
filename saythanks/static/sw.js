/* ==========================================================================
   SayThanks.io — Progressive Web App (PWA) Service Worker
   Offline-first caching, shell resilience, and background sync support.
   ========================================================================== */

const CACHE_VERSION = 'saythanks-v3';
const STATIC_ASSETS = [
  '/',
  '/thanks',
  '/compose-offline',
  '/static/manifest.json',
  '/static/css/normalize.css',
  '/static/css/skeleton.css',
  '/static/css/saythanks.css',
  '/static/css/carbonads.css',
  '/static/css/jquery.modal.min.css',
  '/static/js/main.js',
  '/static/js/jquery.autogrowtextarea.min.js',
  '/static/js/jquery.simplyCountable.js',
  '/static/js/jquery.modal.min.js',
  '/static/js/offline-outbox.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/images/owly.svg',
  '/static/images/inbox.png'
];

const ALLOWED_CDN_HOSTS = new Set([
  'fonts.googleapis.com',
  'fonts.gstatic.com',
  'ajax.googleapis.com',
  'uicdn.toast.com',
  'cdnjs.cloudflare.com'
]);

// 1. Install: Pre-cache core local application shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate: Clean up older cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_VERSION) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch: Safe caching strategy
self.addEventListener('fetch', (event) => {
  const request = event.request;

  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  // Strategy A: Static assets & fonts -> Cache-first with network fallback
  if (
    url.pathname.startsWith('/static/') ||
    ALLOWED_CDN_HOSTS.has(url.hostname)
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_VERSION).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return networkResponse;
        }).catch(() => {
          // Provide clean fallback Response instead of undefined
          return new Response('', { status: 408, statusText: 'Offline' });
        });
      })
    );
    return;
  }

  // Strategy B: Navigation & Public HTML Pages only
  // Avoid caching authenticated pages like /inbox or account settings
  const isPublicPage = url.pathname === '/' ||
                       url.pathname === '/thanks' ||
                       url.pathname === '/privacy' ||
                       url.pathname === '/compose-offline' ||
                       url.pathname.startsWith('/to/');

  if (!isPublicPage) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_VERSION).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(async () => {
        const cached = await caches.match(request);
        if (cached) {
          return cached;
        }
        if (url.pathname.startsWith('/to/')) {
          const composeFallback = await caches.match('/compose-offline');
          if (composeFallback) {
            return composeFallback;
          }
        }
        const fallback = await caches.match('/');
        if (fallback) {
          return fallback;
        }
        return new Response('<h1>SayThanks is currently offline</h1><p>Notes will sync once reconnected.</p>', {
          status: 503,
          headers: { 'Content-Type': 'text/html' }
        });
      })
  );
});

// 4. Background Sync: Auto-drain offline outbox when network returns
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-saythanks-outbox') {
    event.waitUntil(
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'TRIGGER_OUTBOX_SYNC' });
        });
      })
    );
  }
});
