import { useAuth } from "@/context/auth/auth-context-utils";
import { tokenCookies } from "@/utils/cookies";
import { isEncryptionSupported } from "@/utils/helper";
import { useEffect, useRef, useState, useCallback } from "react";

const CHAT_SERVICE_URL =
  (import.meta.env.VITE_API_CHAT_SOCKET as string) ||
  "ws://139.59.25.254/backend/chat-service";

export const useChatSocket = (roomId: string | null) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const roomIdRef = useRef(roomId);
  const { user } = useAuth();
  const userIdRef = useRef(user?.id);

  useEffect(() => {
    roomIdRef.current = roomId;
  }, [roomId]);

  useEffect(() => {
    userIdRef.current = user?.id;
  }, [user?.id]);

  const cleanup = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.onopen = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    const token = tokenCookies.getAccessToken();

    if (!roomId || !token) {
      return;
    }

    cleanup();

    try {
      const wsUrl = `${CHAT_SERVICE_URL}/ws/chat/${roomId}?token=${token}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;

        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          } else {
            if (pingIntervalRef.current) {
              clearInterval(pingIntervalRef.current);
              pingIntervalRef.current = null;
            }
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case "message":
              if (data.sender_id === userIdRef.current) {
                // Server echo of our own sent message — replace the optimistic entry
                setMessages((prev) => {
                  const idx = prev.findIndex((m) => m._optimistic);
                  if (idx !== -1) {
                    const updated = [...prev];
                    updated[idx] = { ...data, _optimistic: false };
                    return updated;
                  }
                  // No optimistic entry — skip since we already have it or it was already replaced
                  return prev;
                });
              } else {
                // Incoming message from the other person — just append
                setMessages((prev) => [...prev, data]);
              }
              break;

            case "message_sent":
              // Server confirmation — update optimistic message with real ID if still pending
              if (data.message_id) {
                setMessages((prev) => {
                  const idx = prev.findIndex((m) => m._optimistic);
                  if (idx !== -1) {
                    const updated = [...prev];
                    updated[idx] = {
                      ...updated[idx],
                      message_id: data.message_id,
                      _optimistic: false,
                    };
                    return updated;
                  }
                  return prev;
                });
              }
              break;

            case "typing":
              if (data.sender_id !== userIdRef.current) {
                setIsTyping(data.is_typing);
              }
              break;

            case "pong":
              break;

            case "error":
              setError(data.message);
              console.error("Chat error:", data.message);
              break;

            default:
              console.log("Unknown message type:", data.type);
          }
        } catch (err) {
          console.error("Error parsing message:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setError("Connection error occurred");
      };

      ws.onclose = (event) => {
        console.log("WebSocket disconnected:", event.code, event.reason);
        setIsConnected(false);

        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        if (
          roomIdRef.current &&
          reconnectAttempts.current < maxReconnectAttempts
        ) {
          reconnectAttempts.current += 1;
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttempts.current),
            30000,
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(
              `Reconnecting... Attempt ${reconnectAttempts.current}`,
            );
            connect();
          }, delay);
        } else if (!roomIdRef.current) {
          console.log("WebSocket closed - roomId is null, not reconnecting");
        } else {
          setError("Failed to reconnect. Please refresh the page.");
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError("Failed to connect to chat service");
    }
  }, [roomId, cleanup]);

  useEffect(() => {
    if (roomId) {
      setMessages([]);
      setIsTyping(false);
      setError(null);
      reconnectAttempts.current = 0;
      connect();
    }

    return () => {
      cleanup();
      reconnectAttempts.current = maxReconnectAttempts;
    };
  }, [roomId, connect, cleanup]);

  const sendMessage = useCallback(
    (message: string, messageType = "text") => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError("Not connected to chat");
        return false;
      }

      try {
        wsRef.current.send(
          JSON.stringify({
            type: "message",
            message,
            message_type: messageType,
            is_client_encrypted: isEncryptionSupported,
          }),
        );

        // Optimistically add the sent message so it renders immediately
        const optimisticMessage = {
          type: "message",
          message_id: `temp-${Date.now()}`,
          message,
          message_type: messageType,
          sender_id: userIdRef.current,
          timestamp: new Date().toISOString(),
          _optimistic: true,
        };
        setMessages((prev) => [...prev, optimisticMessage]);

        return true;
      } catch (err) {
        console.error("Error sending message:", err);
        return false;
      }
    },
    [],
  );

  const sendTyping = useCallback((isTyping: boolean) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: "typing",
        is_typing: isTyping,
      }),
    );
  }, []);

  return { messages, isConnected, error, isTyping, sendMessage, sendTyping };
};
