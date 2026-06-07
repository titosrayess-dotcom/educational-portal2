const CACHE_NAME = "educational-portal-v1";
const urlsToCache = [
  "/",
  "/index.html",
  "/assets/css/style-main.css",
  "/assets/css/style-section-header.css",
  "/assets/css/style-sector.css",
  "/assets/js/main.js",
  "/assets/js/searchData.js",
  "/assets/js/sector.js"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(cacheNames => Promise.all(
      cacheNames.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))
    ))
  );
});
