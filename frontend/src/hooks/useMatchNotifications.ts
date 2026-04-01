import { useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";

const MAX_RECONNECT_DELAY_MS = 30_000;

/**
 * Connects a WebSocket to the user service and calls `onMatchReady`
 * whenever the server pushes a `matches_ready` notification.
 * Reconnects automatically with exponential backoff.
 */
export function useMatchNotifications(onMatchReady: () => void) {
  const { user } = useAuth();
  const callbackRef = useRef(onMatchReady);
  callbackRef.current = onMatchReady;

  useEffect(() => {
    if (!user) return;

    let ws: WebSocket | null = null;
    let attempt = 0;
    let timer: ReturnType<typeof setTimeout>;
    let stopped = false;

    async function connect() {
      if (stopped) return;

      const token = await user!.getIdToken();
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/api/user/ws?token=${token}`);

      ws.onopen = () => {
        attempt = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "matches_ready") {
            callbackRef.current();
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (stopped) return;
        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS);
        attempt++;
        timer = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      stopped = true;
      clearTimeout(timer);
      ws?.close();
    };
  }, [user]);
}
