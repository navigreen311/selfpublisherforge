/**
 * useWebSocket — React hook wrapping WebSocketManager.
 *
 * Usage:
 *   const { isConnected, lastMessage, sendMessage } = useWebSocket("writing", bookId);
 *
 * Automatically connects on mount and disconnects on unmount.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ConnectionState,
  WebSocketManager,
  WSChannel,
  WSMessage,
} from "@/lib/websocket";

export interface UseWebSocketReturn {
  /** Whether the WebSocket is currently connected. */
  isConnected: boolean;
  /** Current connection state. */
  connectionState: ConnectionState;
  /** The most recent message received from the server. */
  lastMessage: WSMessage | null;
  /** Send a JSON message through the WebSocket. */
  sendMessage: (message: Record<string, unknown>) => void;
}

export interface UseWebSocketOptions {
  /** If false, the hook will not connect automatically (default: true). */
  enabled?: boolean;
}

export function useWebSocket(
  channel: WSChannel,
  roomId: string,
  options?: UseWebSocketOptions,
): UseWebSocketReturn {
  const { enabled = true } = options ?? {};

  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const managerRef = useRef<WebSocketManager | null>(null);

  // Stable send callback.
  const sendMessage = useCallback(
    (message: Record<string, unknown>) => {
      managerRef.current?.send(message);
    },
    [],
  );

  useEffect(() => {
    if (!enabled || !roomId) return;

    // Read the JWT from localStorage (mirrors api.ts pattern).
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token") ?? ""
        : "";

    const mgr = new WebSocketManager(channel, roomId, token);
    managerRef.current = mgr;

    const unsubState = mgr.onStateChange((state) => {
      setConnectionState(state);
    });

    const unsubMsg = mgr.onMessage((msg) => {
      setLastMessage(msg);
    });

    mgr.connect();

    return () => {
      unsubState();
      unsubMsg();
      mgr.disconnect();
      managerRef.current = null;
    };
  }, [channel, roomId, enabled]);

  return {
    isConnected: connectionState === "connected",
    connectionState,
    lastMessage,
    sendMessage,
  };
}
