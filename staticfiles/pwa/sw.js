// static/sw.js - Service Worker for Abuja Rentals
const CACHE_NAME = 'abuja-rentals-v3';
const OFFLINE_URL = '/offline/';

// Assets to cache on install - use relative paths
const PRECACHE_ASSETS = [
  '/',
  '/offline/',
  '/manifest.json',
  '/serviceworker.js'
  // Remove external URLs from precache
];

// Install event
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Caching app shell');
        // Try to add each asset individually to catch failures
        return Promise.allSettled(
          PRECACHE_ASSETS.map(url => 
            fetch(url)
              .then(response => {
                if (response.ok) {
                  return cache.put(url, response);
                }
                throw new Error(`Failed to fetch ${url}: ${response.status}`);
              })
              .catch(error => {
                console.warn(`[ServiceWorker] Failed to cache ${url}:`, error);
              })
          )
        ).then(() => cache);
      })
      .then(() => self.skipWaiting())
      .catch(error => {
        console.error('[ServiceWorker] Install failed:', error);
      })
  );
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[ServiceWorker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip API calls and admin URLs for freshness
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/admin/') || 
      url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/logout')) {
    return;
  }

  // Special handling for offline page
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached response if found
        if (response) {
          return response;
        }

        return fetch(event.request)
          .then(response => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200) {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            // Cache the response
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              })
              .catch(error => {
                console.warn('[ServiceWorker] Cache put failed:', error);
              });

            return response;
          })
          .catch(error => {
            console.log('[ServiceWorker] Fetch failed:', error);
            // If network fails, try to serve from cache
            return caches.match(event.request);
          });
      })
  );
});

// Handle messages
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});