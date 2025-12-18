function getScopePath() {
  // e.g. scope https://example.com/v2/ => "/v2/"
  try {
    return new URL(self.registration.scope).pathname;
  } catch {
    return '/';
  }
}

const DEBUG =
  self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1';
const log = (...args) => {
  if (DEBUG) console.log(...args);
};

const SCOPE_PATH = getScopePath();
const CACHE_KEY = SCOPE_PATH.replace(/[^a-zA-Z0-9_-]/g, '_');
const CACHE_NAME = 'lit-up-static-' + CACHE_KEY;
const AUDIO_CACHE_NAME = 'lit-up-audio-' + CACHE_KEY;

// Files to cache for offline functionality
const STATIC_CACHE_FILES = [
  // Cache relative to service worker scope so /v1/ and /v2/ don't conflict
  new URL('./', self.registration.scope).toString(),
  new URL('index.html', self.registration.scope).toString(),
  new URL('favicon.svg', self.registration.scope).toString(),
  new URL('favicon-32x32.png', self.registration.scope).toString(),
  new URL('appConfig.json', self.registration.scope).toString(),
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  log('Service Worker: Installing...');
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => {
        log('Service Worker: Caching static files');
        return cache.addAll(STATIC_CACHE_FILES);
      })
      .then(() => {
        log('Service Worker: Installation complete');
        return self.skipWaiting();
      }),
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  log('Service Worker: Activating...');
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== AUDIO_CACHE_NAME) {
              log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          }),
        );
      })
      .then(() => {
        log('Service Worker: Activation complete');
        return self.clients.claim();
      }),
  );
});

// Fetch event - handle requests
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle audio files with special caching strategy
  if (request.destination === 'audio' || url.pathname.includes('.mp3')) {
    event.respondWith(
      caches.open(AUDIO_CACHE_NAME).then((cache) => {
        return cache.match(request).then((response) => {
          if (response) {
            log('Service Worker: Serving audio from cache:', url.pathname);
            return response;
          }

          return fetch(request)
            .then((fetchResponse) => {
              // Cache successful audio responses
              if (fetchResponse.status === 200) {
                log('Service Worker: Caching audio file:', url.pathname);
                cache.put(request, fetchResponse.clone());
              }
              return fetchResponse;
            })
            .catch((error) => {
              log('Service Worker: Audio fetch failed:', error);
              // Return a fallback or error response
              return new Response('Audio not available offline', {
                status: 503,
                statusText: 'Service Unavailable',
              });
            });
        });
      }),
    );
    return;
  }

  // Handle other requests with cache-first strategy
  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        log('Service Worker: Serving from cache:', url.pathname);
        return response;
      }

      return fetch(request)
        .then((fetchResponse) => {
          // Don't cache non-successful responses
          if (
            !fetchResponse ||
            fetchResponse.status !== 200 ||
            fetchResponse.type !== 'basic'
          ) {
            return fetchResponse;
          }

          // Cache successful responses
          const responseToCache = fetchResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });

          return fetchResponse;
        })
        .catch((error) => {
          log('Service Worker: Fetch failed:', error);
          // Return offline page for navigation requests
          if (request.mode === 'navigate') {
            return caches.match('/index.html');
          }
          throw error;
        });
    }),
  );
});

// Background sync for better audio handling
self.addEventListener('sync', (event) => {
  if (event.tag === 'audio-sync') {
    log('Service Worker: Background sync for audio');
    event.waitUntil(
      // Handle any pending audio operations
      Promise.resolve(),
    );
  }
});

// Push notifications (for future use)
self.addEventListener('push', () => {
  log('Service Worker: Push notification received');
  // Handle push notifications if needed
});

// Message handling from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
