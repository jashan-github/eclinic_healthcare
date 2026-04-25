import { useEffect, useRef, useState } from "react";
import { PaperPlaneTiltIcon, XIcon } from "@phosphor-icons/react";
import type { ChatMessage } from "@/hooks/use-webinar-rtm";

interface WebinarChatPanelProps {
  chatMessages: ChatMessage[];
  onSendMessage: (text: string) => void;
  currentUserId: string;
  onClose: () => void;
}

const WebinarChatPanel = ({
  chatMessages,
  onSendMessage,
  currentUserId,
  onClose,
}: WebinarChatPanelProps) => {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (timestamp: number) => {
    const d = new Date(timestamp);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700">
        <span className="text-white font-semibold">Chat</span>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition"
        >
          <XIcon size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {chatMessages.map((msg) => (
          <div key={msg.id}>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-sm font-medium ${
                  msg.senderId === currentUserId
                    ? "text-green-400"
                    : "text-blue-400"
                }`}
              >
                {msg.senderName}
              </span>
              <span className="text-xs text-gray-500">
                {formatTime(msg.timestamp)}
              </span>
            </div>
            <p className="text-gray-200 text-sm mt-0.5 wrap-break-words">
              {msg.text}
            </p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            className="flex-1 bg-gray-700 text-white text-sm rounded-lg px-3 py-2 outline-none placeholder-gray-400 focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white transition"
          >
            <PaperPlaneTiltIcon size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default WebinarChatPanel;
