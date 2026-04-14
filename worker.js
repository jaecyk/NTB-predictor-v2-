addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});
async function handleRequest(request) {
  const b = "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImVuIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9IlVURi04Ij4KPG1ldGEgbmFtZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCwgaW5pdGlhbC1zY2FsZT0xLjAiPgo8dGl0bGU+TmlnZXJpYSBBdWN0aW9uIFJhdGUgUHJlZGljdG9yPC90aXRsZT4KPC9oZWFkPgo8Ym9keT4KPHNjcmlwdD4KbG9jYXRpb24uaHJlZiA9ICJodHRwczovL25nYS1hdWN0aW9uLXByZWRpY3Rvci5wYWdlcy5kZXYiOwk8L3NjcmlwdD4KPC9ib2R5Pgo8L2h0bWw+";
  return new Response(atob(b), {headers: {"Content-Type": "text/html;charset=UTF-8"}});
}
