const CACHE_NAME = "saythanks-public-v4";
const OFFLINE_URL = "/static/offline.html";
const PRECACHE_URLS = [
  OFFLINE_URL,
  "/thanks",
  "/static/manifest.json",
  "/static/css/normalize.css",
  "/static/css/skeleton.css",
  "/static/css/saythanks.css",
  "/static/js/main.js",
  "/static/images/owly.svg",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

function isPublicRequest(request) {
  const url = new URL(request.url);
  const trustedExternalOrigins = [
    "https://uicdn.toast.com",
    "https://ajax.googleapis.com",
    "https://cdnjs.cloudflare.com",
    "https://fonts.googleapis.com",
    "https://fonts.gstatic.com",
  ];

  if (
    request.method !== "GET" ||
    (url.origin !== self.location.origin &&
      !trustedExternalOrigins.includes(url.origin))
  ) {
    return false;
  }

  if (url.origin !== self.location.origin) {
    return true;
  }

  return ![
    "/inbox",
    "/inbox/",
    "/inbox/search",
    "/inbox/archived",
    "/logout",
    "/callback",
  ].some(
    (path) => url.pathname === path || url.pathname.startsWith(`${path}/`),
  );
}

function matchCachedNavigation(request) {
  const url = new URL(request.url);
  return caches.match(request).then((cachedResponse) => {
    if (cachedResponse || url.pathname !== "/thanks") {
      return cachedResponse;
    }
    return caches.match("/thanks");
  });
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_NAME)
            .map((cacheName) => caches.delete(cacheName)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  if (!isPublicRequest(event.request)) {
    return;
  }

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.ok) {
            const responseCopy = response.clone();
            caches
              .open(CACHE_NAME)
              .then((cache) => cache.put(event.request, responseCopy));
          }
          return response;
        })
        .catch(() =>
          matchCachedNavigation(event.request).then(
            (cachedResponse) => cachedResponse || caches.match(OFFLINE_URL),
          ),
        ),
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(event.request).then((response) => {
        if (response.ok) {
          const responseCopy = response.clone();
          caches
            .open(CACHE_NAME)
            .then((cache) => cache.put(event.request, responseCopy));
        }
        return response;
      });
    }),
  );
});
