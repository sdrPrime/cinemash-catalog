// CINEMASH service worker — network-first, cache fallback (offline play)
const C = 'cinemash-v1';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(['./cinemash.html'])).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok && e.request.url.startsWith(self.location.origin)) {
        const cl = r.clone(); caches.open(C).then(c => c.put(e.request, cl));
      }
      return r;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
