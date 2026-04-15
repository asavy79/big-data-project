/** Base URL for the nginx gateway (no trailing slash). Used for REST + WebSockets. */
const DEFAULT_GATEWAY = "https://gateway-702721595408.us-central1.run.app";

/** [Career Skill Demand API](https://career-backend-702721595408.us-central1.run.app/docs) — occupations & skills explore data. */
const DEFAULT_CAREER_API = "https://career-backend-702721595408.us-central1.run.app";

export const gatewayBaseUrl: string =
  import.meta.env.VITE_GATEWAY_URL !== undefined
    ? import.meta.env.VITE_GATEWAY_URL.replace(/\/$/, "")
    : DEFAULT_GATEWAY;

/**
 * Career backend base URL (no trailing slash).
 * In dev, Vite proxies `/career-api` → career backend (see vite.config.ts) because the API does not send CORS headers.
 * Override with `VITE_CAREER_API_URL` for a custom proxy or tunnel.
 */
export const careerApiBaseUrl: string = (() => {
  const fromEnv = import.meta.env.VITE_CAREER_API_URL;
  if (fromEnv !== undefined && String(fromEnv).trim() !== "") {
    return String(fromEnv).replace(/\/$/, "");
  }
  if (import.meta.env.DEV) {
    return "/career-api";
  }
  return DEFAULT_CAREER_API;
})();

export function gatewayWebSocketUrl(pathAndQuery: string): string {
  if (!gatewayBaseUrl) {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}${pathAndQuery}`;
  }
  const u = new URL(gatewayBaseUrl);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  return `${u.origin}${pathAndQuery}`;
}
