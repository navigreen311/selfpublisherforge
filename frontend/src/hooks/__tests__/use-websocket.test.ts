import { renderHook, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// ─── Mocks ──────────────────────────────────────────────────────────────────

// Track instances and their callbacks for assertions
const mockConnect = jest.fn();
const mockDisconnect = jest.fn();
const mockSend = jest.fn();
const mockOnMessage = jest.fn();
const mockOnStateChange = jest.fn();

// Store the latest callbacks registered by the hook
let capturedStateHandler: ((state: string) => void) | null = null;
let capturedMessageHandler: ((msg: Record<string, unknown>) => void) | null =
  null;

const mockUnsubState = jest.fn();
const mockUnsubMsg = jest.fn();

jest.mock("@/lib/websocket", () => ({
  WebSocketManager: jest.fn().mockImplementation(() => {
    return {
      connect: mockConnect,
      disconnect: mockDisconnect,
      send: mockSend,
      onMessage: mockOnMessage.mockImplementation(
        (handler: (msg: Record<string, unknown>) => void) => {
          capturedMessageHandler = handler;
          return mockUnsubMsg;
        }
      ),
      onStateChange: mockOnStateChange.mockImplementation(
        (handler: (state: string) => void) => {
          capturedStateHandler = handler;
          return mockUnsubState;
        }
      ),
    };
  }),
}));

// Mock localStorage
const mockGetItem = jest.fn().mockReturnValue("test-jwt-token");
Object.defineProperty(window, "localStorage", {
  value: { getItem: mockGetItem },
  writable: true,
});

// ─── Import after mocks ─────────────────────────────────────────────────────

import { useWebSocket } from "../use-websocket";
import { WebSocketManager } from "@/lib/websocket";

// ─── Tests ──────────────────────────────────────────────────────────────────

describe("useWebSocket", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    capturedStateHandler = null;
    capturedMessageHandler = null;
  });

  it("connects to websocket URL on mount", () => {
    renderHook(() => useWebSocket("writing", "room-123"));

    // Should create a WebSocketManager with the correct channel, roomId, and token
    expect(WebSocketManager).toHaveBeenCalledWith(
      "writing",
      "room-123",
      "test-jwt-token"
    );

    // Should call connect on the manager
    expect(mockConnect).toHaveBeenCalledTimes(1);
  });

  it("handles messages from the websocket", () => {
    const { result } = renderHook(() => useWebSocket("writing", "room-123"));

    // Initially lastMessage should be null
    expect(result.current.lastMessage).toBeNull();

    // Simulate receiving a message via the captured handler
    const testMessage = { type: "update", data: { content: "hello" } };
    act(() => {
      capturedMessageHandler?.(testMessage);
    });

    expect(result.current.lastMessage).toEqual(testMessage);
  });

  it("reconnects on disconnect by tracking connection state changes", () => {
    const { result } = renderHook(() => useWebSocket("writing", "room-123"));

    // Initial state should be disconnected (before any state change callback)
    expect(result.current.connectionState).toBe("disconnected");
    expect(result.current.isConnected).toBe(false);

    // Simulate connection established
    act(() => {
      capturedStateHandler?.("connected");
    });

    expect(result.current.connectionState).toBe("connected");
    expect(result.current.isConnected).toBe(true);

    // Simulate disconnection (WebSocketManager handles reconnect internally)
    act(() => {
      capturedStateHandler?.("disconnected");
    });

    expect(result.current.connectionState).toBe("disconnected");
    expect(result.current.isConnected).toBe(false);

    // Simulate reconnecting
    act(() => {
      capturedStateHandler?.("connecting");
    });

    expect(result.current.connectionState).toBe("connecting");
    expect(result.current.isConnected).toBe(false);
  });

  it("handles connection errors", () => {
    const { result } = renderHook(() => useWebSocket("writing", "room-123"));

    // Simulate an error state
    act(() => {
      capturedStateHandler?.("error");
    });

    expect(result.current.connectionState).toBe("error");
    expect(result.current.isConnected).toBe(false);
  });

  it("disconnects and unsubscribes on unmount", () => {
    const { unmount } = renderHook(() => useWebSocket("writing", "room-123"));

    unmount();

    expect(mockUnsubState).toHaveBeenCalledTimes(1);
    expect(mockUnsubMsg).toHaveBeenCalledTimes(1);
    expect(mockDisconnect).toHaveBeenCalledTimes(1);
  });

  it("does not connect when enabled is false", () => {
    renderHook(() =>
      useWebSocket("writing", "room-123", { enabled: false })
    );

    expect(WebSocketManager).not.toHaveBeenCalled();
    expect(mockConnect).not.toHaveBeenCalled();
  });

  it("provides a sendMessage function", () => {
    const { result } = renderHook(() => useWebSocket("writing", "room-123"));

    const testPayload = { type: "cursor", data: { position: 42 } };
    act(() => {
      result.current.sendMessage(testPayload);
    });

    expect(mockSend).toHaveBeenCalledWith(testPayload);
  });
});
