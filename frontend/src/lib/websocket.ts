/**
 * WebSocketManager — full-featured WebSocket client for the SelfPublisherForge
 * real-time event system.
 *
 * Features:
 * - Auto-reconnect with exponential backoff (capped)
 * - Channel subscription / unsubscription
 * - Typed message handlers
 * - Connection state management
 * - Heartbeat (pong) response
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

export type WSChannel = "writing" | "agents" | "analytics" | "publishing";

export interface WSMessage {
  type: string;
  channel?: WSChannel;
  room_id?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
  [key: string]: unknown;
}

export type MessageHandler = (message: WSMessage) => void;
export type StateChangeHandler = (state: ConnectionState) => void;

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

interface WebSocketManagerOptions {
  /** Base URL of the API server (default: env or localhost:8000) */
  baseUrl?: string;
  /** Maximum number of reconnect attempts (default: Infinity) */
  maxReconnectAttempts?: number;
  /** Initial reconnect delay in ms (default: 1000) */
  initialReconnectDelay?: number;
  /** Maximum reconnect delay in ms (default: 30000) */
  maxReconnectDelay?: number;
  /** Backoff multiplier (default: 2) */
  backoffMultiplier?: number;
}

const DEFAULT_OPTIONS: Required<WebSocketManagerOptions> = {
  baseUrl:
    (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) ||
    "http://localhost:8000",
  maxReconnectAttempts: Infinity,
  initialReconnectDelay: 1000,
  maxReconnectDelay: 30000,
  backoffMultiplier: 2,
};

// ---------------------------------------------------------------------------
// Manager
// ---------------------------------------------------------------------------

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private _state: ConnectionState = "disconnected";
  private _channel: WSChannel;
  private _roomId: string;
  private _token: string;
  private _options: Required<WebSocketManagerOptions>;

  private _messageHandlers: Set<MessageHandler> = new Set();
  private _stateHandlers: Set<StateChangeHandler> = new Set();

  private _reconnectAttempts = 0;
  private _reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private _intentionallyClosed = false;

  constructor(
    channel: WSChannel,
    roomId: string,
    token: string,
    options?: WebSocketManagerOptions,
  ) {
    this._channel = channel;
    this._roomId = roomId;
    this._token = token;
    this._options = { ...DEFAULT_OPTIONS, ...options };
  }

  // -----------------------------------------------------------------------
  // Public API
  // -----------------------------------------------------------------------

  /** Current connection state. */
  get state(): ConnectionState {
    return this._state;
  }

  /** Open the WebSocket connection. */
  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return; // already connected / connecting
    }

    this._intentionallyClosed = false;
    this._setState("connecting");

    const base = this._options.baseUrl.replace(/^http/, "ws");
    const url = `${base}/api/v1/ws/${this._channel}/${this._roomId}?token=${encodeURIComponent(this._token)}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this._reconnectAttempts = 0;
      this._setState("connected");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);

        // Respond to server pings automatically.
        if (msg.type === "ping") {
          this.send({ type: "pong" });
          return;
        }

        this._messageHandlers.forEach((handler) => {
          try {
            handler(msg);
          } catch {
            // Swallow handler errors so other handlers are not affected.
          }
        });
      } catch {
        // Non-JSON message — ignore.
      }
    };

    this.ws.onerror = () => {
      this._setState("error");
    };

    this.ws.onclose = () => {
      this._setState("disconnected");
      if (!this._intentionallyClosed) {
        this._scheduleReconnect();
      }
    };
  }

  /** Close the WebSocket connection and stop reconnecting. */
  disconnect(): void {
    this._intentionallyClosed = true;
    this._clearReconnectTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._setState("disconnected");
  }

  /** Send a JSON message over the WebSocket. */
  send(message: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  /** Register a message handler. Returns an unsubscribe function. */
  onMessage(handler: MessageHandler): () => void {
    this._messageHandlers.add(handler);
    return () => {
      this._messageHandlers.delete(handler);
    };
  }

  /** Register a state-change handler. Returns an unsubscribe function. */
  onStateChange(handler: StateChangeHandler): () => void {
    this._stateHandlers.add(handler);
    return () => {
      this._stateHandlers.delete(handler);
    };
  }

  // -----------------------------------------------------------------------
  // Internal
  // -----------------------------------------------------------------------

  private _setState(newState: ConnectionState): void {
    if (newState === this._state) return;
    this._state = newState;
    this._stateHandlers.forEach((handler) => {
      try {
        handler(newState);
      } catch {
        // ignore
      }
    });
  }

  private _scheduleReconnect(): void {
    if (this._reconnectAttempts >= this._options.maxReconnectAttempts) {
      this._setState("error");
      return;
    }

    const delay = Math.min(
      this._options.initialReconnectDelay *
        Math.pow(this._options.backoffMultiplier, this._reconnectAttempts),
      this._options.maxReconnectDelay,
    );

    this._reconnectAttempts += 1;

    this._reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private _clearReconnectTimer(): void {
    if (this._reconnectTimer !== null) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }
  }
}
