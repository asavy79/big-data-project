/** Base URL for the nginx gateway (no trailing slash). Used for REST + WebSockets. */
const DEFAULT_GATEWAY = "https://gateway-702721595408.us-central1.run.app";

/** Career Skill Demand API with insights — [docs](https://career-insights-backend-702721595408.us-central1.run.app/docs). */
const DEFAULT_INSIGHTS_API =
  "https://career-insights-backend-702721595408.us-central1.run.app";

export const gatewayBaseUrl: string =
  import.meta.env.VITE_GATEWAY_URL !== undefined
    ? import.meta.env.VITE_GATEWAY_URL.replace(/\/$/, "")
    : DEFAULT_GATEWAY;

/**
 * Insights / career labor-market API base URL (no trailing slash).
 * Called directly from the browser (CORS must allow your frontend origin).
 * Override with `VITE_INSIGHTS_API_URL` or legacy `VITE_CAREER_API_URL`.
 */
export const insightsApiBaseUrl: string = (() => {
  const fromEnv =
    import.meta.env.VITE_INSIGHTS_API_URL ?? import.meta.env.VITE_CAREER_API_URL;
  if (fromEnv !== undefined && String(fromEnv).trim() !== "") {
    return String(fromEnv).replace(/\/$/, "");
  }
  return DEFAULT_INSIGHTS_API;
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
