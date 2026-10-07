import { useEffect, useRef } from 'react';
import { useStore } from '../store';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectDelay = useRef(1000);
  const { setEnvironments, addMetricsSnapshot, setIncidents, setWsConnected } = useStore();

  function getWsUrl(): string {
    if (typeof window === 'undefined') return 'ws://localhost:8000/ws/telemetry';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If on Vite dev server (port 5173), route through Vite proxy or localhost:8000
    const host = window.location.port === '5173' ? 'localhost:8000' : window.location.host;
    return `${protocol}//${host}/ws/telemetry`;
  }

  function connect() {
    try {
      const wsUrl = getWsUrl();
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onopen = () => {
        setWsConnected(true);
        reconnectDelay.current = 1000;
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.environments) setEnvironments(data.environments);
          if (data.metrics) data.metrics.forEach((m: any) => addMetricsSnapshot(m));
          if (data.incidents) setIncidents(data.incidents);
        } catch (e) {
          console.warn('WS parse error', e);
        }
      };
      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
          connect();
        }, reconnectDelay.current);
      };
      ws.onerror = () => {
        ws.close();
      };
    } catch (e) {
      console.error('WS connection error', e);
      setWsConnected(false);
    }
  }

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
