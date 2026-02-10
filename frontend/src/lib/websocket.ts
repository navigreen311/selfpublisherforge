/**
 * WebSocket client utility with auto-reconnect and typed message handling.
 *
 * Usage:
 *   const ws = new WebSocketClient("ws://localhost:8000/ws");
 *   ws.on("agent.task.completed", (data) => { ... });
 *   ws.connect();
 *   ws.send({ type: "subscribe", channel: "agent_tasks" });
 *   ws.close();
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface WebSocketMessage<T = unknown> {
  type: string;
  data: T;
  timestamp?: string;
  correlation_id?: string;
}

export type MessageHandler<T = unknown> = (data: T, message: WebSocketMessage<T>) => void;

export interface WebSocketClientOptions {
  /** Maximum number of reconnect attempts (default: Infinity). */
  maxReconnectAttempts?: number;
  /** Base delay in ms before reconnect (default: 1000). Doubles each attempt. */
  reconnectBaseDelay?: number;
  /** Maximum reconnect delay in ms (default: 30000). */
  reconnectMaxDelay?: number;
  /** Interval in ms between keep-alive pings (default: 30000). 0 disables. */
  pingInterval?: number;
  /** Additional protocols for the WebSocket constructor. */
  protocols?: string | string[];
}

export type ConnectionState = "connecting" | "connected" | "disconnecting" | "disconnected";

export type ConnectionStateHandler = (state: ConnectionState) => void;

// ---------------------------------------------------------------------------
// Implementation
// ---------------------------------------------------------------------------

export class WebSocketClient {
  private url: string;
  private options: Required<WebSocketClientOptions>;
  private socket: WebSocket | null = null;
  private handlers = new Map<string, Set<MessageHandler>>();
  private wildcardHandlers = new Set<MessageHandler>();
  private stateHandlers = new Set<ConnectionStateHandler>();
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private manualClose = false;
  private _state: ConnectionState = "disconnected";

  constructor(url: string, options: WebSocketClientOptions = {}) {
    this.url = url;
    this.options = {
      maxReconnectAttempts: options.maxReconnectAttempts ?? Infinity,
      reconnectBaseDelay: options.reconnectBaseDelay ?? 1000,
      reconnectMaxDelay: options.reconnectMaxDelay ?? 30_000,
      pingInterval: options.pingInterval ?? 30_000,
      protocols: options.protocols ?? [],
    };
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /** Current connection state. */
  get state(): ConnectionState {
    return this._state;
  }

  /** Open the WebSocket connection. Idempotent. */
  connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.manualClose = false;
    this.setState("connecting");

    const protocols = this.options.protocols;
    this.socket = typeof protocols === "string" || (Array.isArray(protocols) && protocols.length > 0)
      ? new WebSocket(this.url, protocols)
      : new WebSocket(this.url);

    this.socket.onopen = this.handleOpen;
    this.socket.onclose = this.handleClose;
    this.socket.onerror = this.handleError;
    this.socket.onmessage = this.handleMessage;
  }

  /** Gracefully close the connection. */
  close(): void {
    this.manualClose = true;
    this.setState("disconnecting");
    this.stopPing();
    this.cancelReconnect();
    if (this.socket) {
      this.socket.close(1000, "Client closed");
      this.socket = null;
    }
    this.setState("disconnected");
  }

  /** Send a typed message over the socket. */
  send<T = unknown>(message: WebSocketMessage<T>): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.warn("[WebSocketClient] Cannot send, socket not open.");
      return;
    }
    this.socket.send(JSON.stringify(message));
  }

  /** Register a handler for a specific message type. */
  on<T = unknown>(type: string, handler: MessageHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    const handlerSet = this.handlers.get(type)!;
    handlerSet.add(handler as MessageHandler);

    // Return unsubscribe function
    return () => {
      handlerSet.delete(handler as MessageHandler);
      if (handlerSet.size === 0) {
        this.handlers.delete(type);
      }
    };
  }

  /** Register a handler that receives ALL messages. */
  onAny<T = unknown>(handler: MessageHandler<T>): () => void {
    this.wildcardHandlers.add(handler as MessageHandler);
    return () => {
      this.wildcardHandlers.delete(handler as MessageHandler);
    };
  }

  /** Register a connection-state change listener. */
  onStateChange(handler: ConnectionStateHandler): () => void {
    this.stateHandlers.add(handler);
    return () => {
      this.stateHandlers.delete(handler);
    };
  }

  /** Remove all handlers for a given message type (or all if no type given). */
  off(type?: string): void {
    if (type) {
      this.handlers.delete(type);
    } else {
      this.handlers.clear();
      this.wildcardHandlers.clear();
    }
  }

  // -----------------------------------------------------------------------
  // Internal event handlers
  // -----------------------------------------------------------------------

  private handleOpen = (): void => {
    this.reconnectAttempts = 0;
    this.setState("connected");
    this.startPing();
  };

  private handleClose = (event: CloseEvent): void => {
    this.stopPing();
    this.setState("disconnected");

    if (!this.manualClose && event.code !== 1000) {
      this.scheduleReconnect();
    }
  };

  private handleError = (_event: Event): void => {
    // Errors are followed by a close event; reconnect logic lives there.
    console.error("[WebSocketClient] Connection error");
  };

  private handleMessage = (event: MessageEvent): void => {
    let parsed: WebSocketMessage;
    try {
      parsed = JSON.parse(event.data as string) as WebSocketMessage;
    } catch {
      console.warn("[WebSocketClient] Failed to parse message:", event.data);
      return;
    }

    const { type, data } = parsed;

    // Type-specific handlers
    const typeHandlers = this.handlers.get(type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => {
        try {
          handler(data, parsed);
        } catch (err) {
          console.error(`[WebSocketClient] Handler error for "${type}":`, err);
        }
      });
    }

    // Wildcard handlers
    this.wildcardHandlers.forEach((handler) => {
      try {
        handler(data, parsed);
      } catch (err) {
        console.error("[WebSocketClient] Wildcard handler error:", err);
      }
    });
  };

  // -----------------------------------------------------------------------
  // Reconnect logic (exponential backoff with jitter)
  // -----------------------------------------------------------------------

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.warn("[WebSocketClient] Max reconnect attempts reached.");
      return;
    }

    const baseDelay = this.options.reconnectBaseDelay;
    const maxDelay = this.options.reconnectMaxDelay;
    const exponential = Math.min(baseDelay * 2 ** this.reconnectAttempts, maxDelay);
    // Add jitter: +/- 20%
    const jitter = exponential * (0.8 + Math.random() * 0.4);
    const delay = Math.round(jitter);

    this.reconnectAttempts += 1;
    console.info(`[WebSocketClient] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private cancelReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.reconnectAttempts = 0;
  }

  // -----------------------------------------------------------------------
  // Keep-alive ping
  // -----------------------------------------------------------------------

  private startPing(): void {
    if (this.options.pingInterval <= 0) return;
    this.pingTimer = setInterval(() => {
      this.send({ type: "ping", data: null });
    }, this.options.pingInterval);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  // -----------------------------------------------------------------------
  // State management
  // -----------------------------------------------------------------------

  private setState(state: ConnectionState): void {
    if (this._state === state) return;
    this._state = state;
    this.stateHandlers.forEach((handler) => {
      try {
        handler(state);
      } catch (err) {
        console.error("[WebSocketClient] State handler error:", err);
      }
    });
  }
}
