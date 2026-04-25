import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { useParams, useNavigate } from "@tanstack/react-router";
import { ChatWindow } from "../chat-window";
import { UserList } from "../user-list";
import { useChatService } from "../../patients/hooks/use-chat-service";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useChatSocket } from "@/features/socket/use-chat-socket";
import { useChatEncryption } from "@/features/socket/use-chat-encryption";
import axiosInstance from "@/lib/api-chat";
import {
  getActiveChats,
  getClosedChats,
} from "../../patients/services/chat-service";

interface ChatMessage {
  id: string;
  chat_room_id: string;
  sender_id: string;
  sender_type: string;
  message_type: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export interface User {
  unread_count?: number;
  id: string;
  name: string;
  status?: string;
  lastMessage: {
    id: string;
    message: string;
    sender_id: string;
    sender_type: string;
    message_type: string;
    created_at: string;
  };
  avatar: string;
  unread: boolean;
  online: boolean;
}

export interface Message {
  id: string;
  text: string;
  sender: "own" | "other";
  time: string; // ISO timestamp
}

const CHATS_PER_PAGE = 15;
const MESSAGES_PER_PAGE = 30;

const MessageContent: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const params: any = useParams({ strict: false }) as { chatId?: string };

  const { data: currentPageMessages, isLoading: isLoadingCurrentPage } =
    useChatService().useRoomMessages(params.chatId);

  const [selectedUserId, setSelectedUserId] = useState<string | null>(
    params.chatId || null,
  );

  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"active" | "closed">("active");

  /* ───────────── Chats (infinite down) ───────────── */

  const [chatPage, setChatPage] = useState(1);
  const [allChats, setAllChats] = useState<any[]>([]);
  const [activeChats, setActiveChats] = useState<any[]>([]);
  const [closedChats, setClosedChats] = useState<any[]>([]);
  const [hasMoreChats, setHasMoreChats] = useState(true);
  const [loadingMoreChats, setLoadingMoreChats] = useState(false);
  const [isLoadingChats, setIsLoadingChats] = useState(true);

  useEffect(() => {
    const fetchBothChats = async () => {
      try {
        setIsLoadingChats(true);
        const [activeData, closedData] = await Promise.all([
          getActiveChats(CHATS_PER_PAGE, 0),
          getClosedChats(CHATS_PER_PAGE, 0),
        ]);

        setActiveChats(activeData?.rooms || []);
        setClosedChats(closedData?.rooms || []);

        // Set allChats based on active tab
        if (activeTab === "active") {
          setAllChats(activeData?.rooms || []);
          setHasMoreChats((activeData?.rooms || []).length === CHATS_PER_PAGE);
        } else {
          setAllChats(closedData?.rooms || []);
          setHasMoreChats((closedData?.rooms || []).length === CHATS_PER_PAGE);
        }
      } catch (error) {
        console.error("Error fetching chats:", error);
      } finally {
        setIsLoadingChats(false);
      }
    };

    // Only fetch on initial mount
    fetchBothChats();
  }, []);

  const loadMoreChats = useCallback(async () => {
    if (!hasMoreChats || loadingMoreChats) return;

    setLoadingMoreChats(true);
    try {
      const offset = chatPage * CHATS_PER_PAGE;
      const fetchFn = activeTab === "active" ? getActiveChats : getClosedChats;
      const res = await fetchFn(CHATS_PER_PAGE, offset);
      const newChats = res?.rooms || [];

      setAllChats((prev) => [...prev, ...newChats]);

      if (activeTab === "active") {
        setActiveChats((prev) => [...prev, ...newChats]);
      } else {
        setClosedChats((prev) => [...prev, ...newChats]);
      }

      setChatPage((p) => p + 1);

      if (newChats.length < CHATS_PER_PAGE) setHasMoreChats(false);
    } catch (e) {
      console.error("Load chats failed", e);
    } finally {
      setLoadingMoreChats(false);
    }
  }, [chatPage, hasMoreChats, loadingMoreChats, activeTab]);

  // Compute displayed chats based on active tab
  const displayedChats = useMemo(() => {
    return activeTab === "active" ? activeChats : closedChats;
  }, [activeTab, activeChats, closedChats]);

  // Update allChats when displayed chats change
  useEffect(() => {
    setAllChats(displayedChats);
    setHasMoreChats(displayedChats.length >= CHATS_PER_PAGE);
    setChatPage(1);
  }, [displayedChats]);

  /* ───────────── Messages (infinite up) ───────────── */

  const [allMessages, setAllMessages] = useState<ChatMessage[]>([]);
  const [hasMoreMessages, setHasMoreMessages] = useState(true);
  const [loadingOlderMessages, setLoadingOlderMessages] = useState(false);

  const messageOffsetRef = useRef(0);
  const isLoadingOlderRef = useRef(false);
  const hasInitialMessagesRef = useRef(false);

  useEffect(() => {
    if (currentPageMessages?.messages) {
      const reversed = [...currentPageMessages.messages].reverse();
      setAllMessages(reversed);

      messageOffsetRef.current = 0;
      hasInitialMessagesRef.current = true;

      setHasMoreMessages(
        currentPageMessages.messages.length === MESSAGES_PER_PAGE,
      );
    }
  }, [currentPageMessages]);

  const loadOlderMessages = useCallback(async () => {
    if (!selectedUserId || !hasMoreMessages || isLoadingOlderRef.current)
      return;

    isLoadingOlderRef.current = true;
    setLoadingOlderMessages(true);

    try {
      const nextOffset = messageOffsetRef.current + MESSAGES_PER_PAGE;
      const { data } = await axiosInstance.get(
        `/api/chat/${selectedUserId}/messages?limit=${MESSAGES_PER_PAGE}&offset=${nextOffset}`,
      );

      const older = data?.messages || [];

      if (older.length) {
        setAllMessages((prev) => [...older.reverse(), ...prev]);
        messageOffsetRef.current = nextOffset;
      }

      if (older.length < MESSAGES_PER_PAGE) setHasMoreMessages(false);
    } catch (e) {
      console.error("Load older messages failed", e);
    } finally {
      isLoadingOlderRef.current = false;
      setLoadingOlderMessages(false);
    }
  }, [selectedUserId, hasMoreMessages]);

  useEffect(() => {
    setAllMessages([]);
    setHasMoreMessages(true);
    hasInitialMessagesRef.current = false;
    messageOffsetRef.current = 0;
  }, [selectedUserId]);

  /* ───────────── Socket + Encryption ───────────── */

  const { decryptMessage } = useChatEncryption(
    selectedUserId,
    "room-secret-key",
  );

  const [displayedMessages, setDisplayedMessages] = useState<Message[]>([]);

  /* ───────────── IntersectionObservers ───────────── */

  const chatsBottomRef = useRef<HTMLDivElement>(null);
  const messagesTopRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) loadMoreChats();
    });
    if (chatsBottomRef.current) {
      obs.observe(chatsBottomRef.current);
    }
    return () => obs.disconnect();
  }, [loadMoreChats]);

  useEffect(() => {
    if (!selectedUserId) return;

    const obs = new IntersectionObserver(
      ([entry]) => {
        if (
          entry.isIntersecting &&
          hasMoreMessages &&
          hasInitialMessagesRef.current &&
          !isLoadingOlderRef.current
        ) {
          const container = messagesContainerRef.current;
          const prevHeight = container?.scrollHeight || 0;
          const prevTop = container?.scrollTop || 0;

          loadOlderMessages().finally(() => {
            requestAnimationFrame(() => {
              if (!container) return;
              container.scrollTop =
                container.scrollHeight - prevHeight + prevTop;
            });
          });
        }
      },
      { rootMargin: "300px 0px 0px 0px" },
    );

    if (messagesTopRef.current) {
      obs.observe(messagesTopRef.current);
    }
    return () => obs.disconnect();
  }, [selectedUserId, hasMoreMessages, loadOlderMessages]);

  /* ───────────── Users ───────────── */

  const users = useMemo<User[]>(() => {
    // Sort chats by last message time (most recent first)
    const sortedChats = [...allChats].sort((a, b) => {
      const timeA = a.last_message?.created_at || a.last_message_at || "0";
      const timeB = b.last_message?.created_at || b.last_message_at || "0";
      return new Date(timeB).getTime() - new Date(timeA).getTime();
    });

    return sortedChats.map((chat) => ({
      id: chat.id,
      name: chat.patient_name || chat.doctor_name || "Unknown",
      avatar: chat.patient_image || chat.doctor_image || "",
      unread: (chat.unread_count || 0) > 0,
      unread_count: chat.unread_count || 0,
      status: chat.status || (activeTab === "closed" ? "closed" : "active"),
      online: false,
      lastMessage: {
        id: chat.last_message?.id || "",
        message: chat.last_message?.message || "",
        sender_id: chat.last_message?.sender_id || "",
        sender_type: chat.last_message?.sender_type || "",
        message_type: chat.last_message?.message_type || "text",
        created_at: chat.last_message?.created_at || "",
      },
    }));
  }, [allChats, activeTab]);

  const filteredUsers = useMemo(
    () =>
      users.filter((u) =>
        u.name.toLowerCase().includes(searchQuery.toLowerCase()),
      ),
    [users, searchQuery],
  );

  const selectedUser = users.find((u) => u.id === selectedUserId);

  // Only connect WebSocket for active chats - NEVER for closed tab
  const shouldConnectSocket = activeTab === "active" && !!selectedUserId;

  const {
    messages: realtimeMessages,
    isConnected,
    isTyping,
    sendMessage,
    sendTyping,
  } = useChatSocket(shouldConnectSocket ? selectedUserId : null);

  const handleSelectUser = (id: string) => {
    setSelectedUserId(id);
    navigate({ to: `/app/messages/${id}` });
  };

  const handleChatClosed = (roomId: string) => {
    // Move the chat from active to closed locally
    const closedChat = activeChats.find((c) => c.id === roomId);
    if (closedChat) {
      setActiveChats((prev) => prev.filter((c) => c.id !== roomId));
      setClosedChats((prev) => [
        { ...closedChat, status: "closed" },
        ...prev,
      ]);
    }

    // If the closed chat was selected, clear selection
    if (selectedUserId === roomId) {
      setSelectedUserId(null);
      navigate({ to: "/app/messages" });
    }

    // Switch to closed tab so user sees the result
    setActiveTab("closed");
  };
  const decryptAndCombine = useCallback(async () => {
    const decrypt = async (msg: any) => {
      const text = await decryptMessage(msg.message);
      return {
        id: msg.id,
        text,
        sender: msg.sender_id === user?.id ? "own" : "other",
        time: msg.created_at,
      };
    };

    const historical = await Promise.all(allMessages.map(decrypt));

    // Build a set of historical message IDs for dedup
    const historicalIds = new Set(historical.map((m) => m.id));

    const realtime = await Promise.all(
      realtimeMessages
        .filter((m: any) => {
          // Skip realtime messages that already exist in historical (REST overlap)
          const id = m.message_id;
          return !id || !historicalIds.has(id);
        })
        .map((m: any) =>
          decrypt({
            ...m,
            id: m.message_id,
            created_at: m.timestamp || new Date().toISOString(),
          }),
        ),
    );

    // Historical messages are already sorted from API.
    // Realtime messages are in insertion order (chronological).
    // Append realtime after historical — no re-sorting needed.
    const combined = [...historical, ...realtime];

    setDisplayedMessages((prev: any) =>
      JSON.stringify(prev) === JSON.stringify(combined) ? prev : combined,
    );
  }, [allMessages, realtimeMessages, decryptMessage, user?.id]);

  useEffect(() => {
    decryptAndCombine();
  }, [decryptAndCombine]);

  if (isLoadingChats && chatPage === 1) {
    return (
      <div className="flex h-full items-center justify-center">Loading…</div>
    );
  }

  const isConnectionConnected =
    activeTab === "closed" || selectedUser?.status === "closed"
      ? "Closed"
      : isConnected
        ? "Connected"
        : "Connecting…";

  return (
    <div className="flex h-full gap-10">
      <UserList
        users={filteredUsers}
        selectedUserId={selectedUserId}
        onSelectUser={handleSelectUser}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        loadMoreRef={chatsBottomRef}
        isLoadingMore={loadingMoreChats}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onChatClosed={handleChatClosed}
      />

      <ChatWindow
        selectedUser={selectedUser}
        messages={displayedMessages}
        isConnected={isConnectionConnected}
        connectionStatus={isConnectionConnected}
        isLoadingMessages={isLoadingCurrentPage}
        isLoadingOlder={loadingOlderMessages}
        isTyping={isTyping}
        messagesTopRef={messagesTopRef}
        scrollContainerRef={messagesContainerRef}
        sendMessage={sendMessage}
        sendTyping={sendTyping}
      />
    </div>
  );
};

export default MessageContent;
