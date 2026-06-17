/** Resource route (no component) for container healthchecks. Returns 200 without touching the corpus. */
export function loader() {
  return new Response("ok", { status: 200, headers: { "content-type": "text/plain" } });
}
