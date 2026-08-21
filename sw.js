// CINEMASH service worker — same-origin only, network-first with cache fallback.
const C = 'cinemash-v4';
self.addEventListener('install', e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(['./cinemash.html'])).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  // Let the browser handle anything off-origin itself — Firebase, gstatic, fonts.
  // Intercepting those was breaking sign-in and the live leaderboard.
  if (!e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok) { const cl = r.clone(); caches.open(C).then(c => c.put(e.request, cl)); }
      return r;
    }).catch(() => caches.match(e.request, { ignoreSearch: true }).then(m => m || Response.error()))
  );
});
