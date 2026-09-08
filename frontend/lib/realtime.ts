"use client";

import { useEffect, useRef, useState } from "react";
import { getToken } from "./auth";
import type { LiveServerMessage, LiveStateMessage, LiveValues } from "./types";

const MAX_POINTS = 120;

export type RealtimeConnectionStatus =
  | "connecting"
  | "running"
  | "paused"
  | "completed"
  | "disconnected";

export interface LiveChartPoint extends LiveValues {
  sequence: number;
  time: string;
  virtual_time: string;
}

function buildWebSocketUrl(scenarioId: number): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
  const url = new URL(`${apiUrl.replace(/\/$/, "")}/realtime/ws/${scenarioId}`);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

function buildWebSocketSubprotocols(): string[] {
  // El JWT viaja como subprotocolo Sec-WebSocket-Protocol, no en el query
  // string, para no exponerlo en logs de proxy, historial ni referrers.
  const token = getToken();
  return token ? [token] : [];
}

export function useRealtimeSimulation(scenarioId: number | null) {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<RealtimeConnectionStatus>("disconnected");
  const [points, setPoints] = useState<LiveChartPoint[]>([]);
  const [lastPoint, setLastPoint] = useState<LiveChartPoint | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (scenarioId === null) return;

    const socket = new WebSocket(buildWebSocketUrl(scenarioId), buildWebSocketSubprotocols());
    socketRef.current = socket;
    setStatus("connecting");
    setPoints([]);
    setLastPoint(null);
    setError(null);

    socket.onopen = () => setStatus("running");
    socket.onmessage = (event) => {
      let message: LiveServerMessage;
      try {
        message = JSON.parse(event.data) as LiveServerMessage;
      } catch {
        setError("El servidor envió un mensaje inválido");
        return;
      }

      if (message.type === "state") {
        const point: LiveChartPoint = {
          ...message.values,
          sequence: message.sequence,
          time: message.virtual_time,
          virtual_time: message.virtual_time,
        };
        setLastPoint(point);
        setPoints((previous) => [...previous, point].slice(-MAX_POINTS));
      } else if (message.type === "status") {
        if (message.status === "paused") setStatus("paused");
        if (message.status === "running" || message.status === "reset") setStatus("running");
        if (message.status === "horizon_reached") setStatus("completed");
      } else if (message.type === "error") {
        setError(message.message);
      }
    };
    socket.onerror = () => setError("No se pudo conectar con el simulador en vivo");
    socket.onclose = () => {
      socketRef.current = null;
      setStatus((current) => current === "completed" ? current : "disconnected");
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [scenarioId]);

  function send(command: Record<string, unknown>) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(command));
    }
  }

  return {
    status,
    points,
    lastPoint,
    error,
    start: () => send({ type: "start" }),
    pause: () => send({ type: "pause" }),
    reset: () => {
      setPoints([]);
      setLastPoint(null);
      send({ type: "reset" });
    },
    setSpeed: (value: number) => send({ type: "set_speed", value }),
  };
}
