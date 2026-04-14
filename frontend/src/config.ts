/** Base URL for the nginx gateway (no trailing slash). Used for REST + WebSockets. */
const DEFAULT_GATEWAY = "https://gateway-702721595408.us-central1.run.app";

export const gatewayBaseUrl: string =
  import.meta.env.VITE_GATEWAY_URL !== undefined
    ? import.meta.env.VITE_GATEWAY_URL.replace(/\/$/, "")
    : DEFAULT_GATEWAY;

export function gatewayWebSocketUrl(pathAndQuery: string): string {
  if (!gatewayBaseUrl) {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}${pathAndQuery}`;
  }
  const u = new URL(gatewayBaseUrl);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  return `${u.origin}${pathAndQuery}`;
}
