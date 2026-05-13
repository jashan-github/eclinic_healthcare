// 3. src/components/chat-window.tsx  (updated)

import { Textarea } from "@mantine/core";
import { PaperPlaneTiltIcon } from "@phosphor-icons/react";
import { useState, useRef, useEffect } from "react";
import { toast } from "react-toastify";
import type { Message, User } from "./components/message-content";
import { useChatEncryption } from "@/features/socket/use-chat-encryption";
import { formatDateTime } from "@/utils/helper";

const MAX_MESSAGE_LENGTH = 5000;

interface ChatWindowProps {
  selectedUser: User | undefined;
  messages: Message[];
  isConnected: string;
  connectionStatus: string;
  isLoadingMessages: boolean;
  isLoadingOlder: boolean;
  isTyping: boolean;
  messagesTopRef: React.RefObject<HTMLDivElement | null>;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  sendMessage: (message: string, messageType?: string) => boolean;
  sendTyping: (isTyping: boolean) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  selectedUser,
  messages,
  isConnected,
  isLoadingMessages,
  isLoadingOlder,
  isTyping,
  messagesTopRef,
  scrollContainerRef,
  sendMessage,
  sendTyping,
}) => {
  const [newMessage, setNewMessage] = useState("");
  const [messageError, setMessageError] = useState<string | null>(null);
  const typingTimeoutRef = useRef<null | NodeJS.Timeout>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { encryptMessage } = useChatEncryption(
    selectedUser?.id || null,
    "room-secret-key",
  );

  const handleTyping = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setNewMessage(value);
    setMessageError(
      value.length > MAX_MESSAGE_LENGTH
        ? `Message must be ${MAX_MESSAGE_LENGTH} characters or fewer`
        : null,
    );
    if (!selectedUser?.id) return;

    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    sendTyping(true);
    typingTimeoutRef.current = setTimeout(() => sendTyping(false), 2000);
  };

  const handleSend = async () => {
    const trimmed = newMessage.trim();
    if (!trimmed) {
      setMessageError("Message cannot be empty");
      return;
    }
    if (!selectedUser?.id) return;
    if (trimmed.length > MAX_MESSAGE_LENGTH) {
      const errorMessage = `Message is too long (max ${MAX_MESSAGE_LENGTH} characters)`;
      setMessageError(errorMessage);
      toast.error(errorMessage);
      return;
    }
    const encrypted = await encryptMessage(newMessage);
    const success = sendMessage(encrypted);
    if (success) {
      setNewMessage("");
      setMessageError(null);
      sendTyping(false);
    }
  };

  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (!selectedUser) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">Chat</div>
          <h3 className="font-poppins font-semibold text-xl leading-6 text-[#020817]">
            Select a conversation
          </h3>
          <p className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
            Choose a conversation from the list to start messaging
          </p>
        </div>
      </div>
    );
  }

  if (isLoadingMessages && messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        Loading messages...
      </div>
    );
  }

  return (
    <div className="p-4 max-h-[600px] flex-1 flex flex-col bg-white border border-[#E2E8F0] rounded-lg">
      <div className="bg-white rounded-lg">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="font-poppins font-semibold text-xl leading-6 text-[#020817]">
              General Inbox
            </div>
            <div className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
              Secure messaging with your healthcare provider
              <span className={
                isConnected === "Connected" ? "text-green-600" :
                isConnected === "Closed" ? "text-red-500" :
                "text-blue-500"
              }> {isConnected}</span>
            </div>
          </div>
        </div>
      </div>

      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto mt-4 flex flex-col space-y-2"
      >
        {isLoadingOlder && (
          <div className="py-4 text-center text-sm text-gray-500">
            Loading older messages...
          </div>
        )}

        <div ref={messagesTopRef} className="min-h-[1px]" />

        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-20">No messages yet</div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.sender === "own" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-xs md:max-w-md px-6 py-3 space-y-2 rounded-md ${
                  message.sender === "own"
                    ? "bg-[#002FD4] text-white"
                    : "bg-[#F1F5F9] text-gray-900 border border-gray-200"
                }`}
              >
                <p
                  className={`${
                    message.sender === "own"
                      ? "font-poppins font-normal text-sm leading-5 text-[#F8FAFC]"
                      : "font-poppins font-normal text-sm leading-5 text-[#020817]"
                  }`}
                >
                  {message.text}
                </p>
                <p
                  className={`text-xs mt-1 ${message.sender === "own" ? "text-blue-100" : "text-gray-500"}`}
                >
                  {formatDateTime(message.time)}
                </p>
              </div>
            </div>
          ))
        )}

        {isTyping && (
          <div className="px-4 py-2 text-gray-500 text-sm sticky bottom-0 bg-white">
            Typing...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {selectedUser.status === "active" ? (
        <div className="space-y-2 py-4 bg-white border-t border-gray-200">
          <div className="flex">
            <Textarea
              placeholder="Type your message..."
              value={newMessage}
              onChange={handleTyping}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              maxLength={MAX_MESSAGE_LENGTH}
              error={messageError}
              rows={1}
              autosize={false}
              radius="md"
              size="md"
              variant="unstyled"
              style={{ width: "100%" }}
              styles={{
                wrapper: { overflowY: "auto", scrollbarWidth: "thin" },
                input: {
                  backgroundColor: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  fontFamily: "Poppins, sans-serif",
                  fontWeight: 400,
                  fontSize: "14px",
                  color: "#64748B",
                  padding: "12px 16px",
                  resize: "none",
                  "::placeholder": { color: "#64748B", opacity: 1 },
                },
              }}
            />
            <button
              onClick={handleSend}
              disabled={!newMessage.trim() || newMessage.trim().length > MAX_MESSAGE_LENGTH}
              className={`-translate-x-1 pr-6 pl-4 py-3 text-white rounded-md transition-colors flex items-center gap-2 ${
                newMessage.trim()
                  ? "bg-[#002FD4] hover:bg-[#002FD4]/90"
                  : "bg-[#8097E9] cursor-not-allowed"
              }`}
            >
              <PaperPlaneTiltIcon className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-2 font-poppins font-normal text-xs leading-4 text-[#64748B]">
            Press Enter to send, Shift+Enter for new line · {newMessage.length}/{MAX_MESSAGE_LENGTH}
          </div>
        </div>
      ) : (
        <span className="text-center text-red-400">Conversation End</span>
      )}
    </div>
  );
};
