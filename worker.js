addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const api = "https://web-production-fe355.up.railway.app";
  const path = new URL(request.url).pathname;
  
  // Proxy API calls to Railway
  if (path.startsWith("/predict") || path.startsWith("/predictions") || path.startsWith("/health") || path.startsWith("/snapshots")) {
    const target = api + request.url.replace(new URL(request.url).origin, "");
    return fetch(target, {
      method: request.method,
      headers: request.headers,
      body: request.body
    });
  }
  
  // Serve dashboard for everything else
  return fetch("https://nga-auction-v2.pages.dev/");
}
