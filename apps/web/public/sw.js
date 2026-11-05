/* RoboWiki service worker: pages network-first, static stale-while-revalidate, API network-only. */
const CACHE = 'robowiki-v1'
const PRECACHE = ['/', '/catalog.html', '/manifest.webmanifest']

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', event => {
  const { request } = event
  if (request.method !== 'GET') return
  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/')) return

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(res => {
          const copy = res.clone()
          caches.open(CACHE).then(cache => cache.put(request, copy))
          return res
        })
        .catch(() => caches.match(request).then(hit => hit || caches.match('/'))),
    )
    return
  }

  if (/\.(?:css|js|png|jpe?g|webp|svg|woff2?|ico)$/.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then(hit => {
        const network = fetch(request).then(res => {
          if (res.ok) {
            const copy = res.clone()
            caches.open(CACHE).then(cache => cache.put(request, copy))
          }
          return res
        }).catch(() => hit)
        return hit || network
      }),
    )
  }
})
