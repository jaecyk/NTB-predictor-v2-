addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = "https://web-production-fe355.up.railway.app";
  const path = new URL(request.url).pathname;
  const target = path === "/" ? url + "/predict" : url + path;
  return fetch(target, request);
}
