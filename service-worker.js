// Mon cap — service worker
// Deux stratégies :
//   • abris.json  -> RÉSEAU-D'ABORD (donnée vivante : fraîche si en ligne, dernière copie sinon)
//   • le reste    -> CACHE-FIRST   (coquille : HTML, icônes, opening_hours.js, manifeste)

const CACHE = 'mon-cap-v10';
const CORE = [
  './',
  './index.html',
  './manifest.json',
  './opening_hours.js',
  './icons/icon-192x192.png',
  './icons/icon-512x512.png'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(CORE); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.map(function (k) {
          return k === CACHE ? null : caches.delete(k);
        }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;

  var url = new URL(e.request.url);

  // --- abris.json : réseau-d'abord ---
  if (url.pathname.indexOf('abris.json') !== -1) {
    e.respondWith(
      fetch(e.request).then(function (resp) {
        if (resp && resp.ok) {
          var copy = resp.clone();
          // on stocke sous une clé canonique (sans ?t=...) pour un repli fiable
          caches.open(CACHE).then(function (c) { c.put('./abris.json', copy); }).catch(function () {});
        }
        return resp;
      }).catch(function () {
        // hors-ligne : on rend la dernière copie enregistrée
        return caches.match('./abris.json');
      })
    );
    return;
  }

  // --- coquille : cache-first ---
  e.respondWith(
    caches.match(e.request).then(function (hit) {
      if (hit) return hit;
      return fetch(e.request).then(function (resp) {
        var copy = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(e.request, copy); }).catch(function () {});
        return resp;
      }).catch(function () {
        return caches.match('./index.html');
      });
    })
  );
});
