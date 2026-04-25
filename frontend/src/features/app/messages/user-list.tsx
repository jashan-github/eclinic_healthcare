// user-list.tsx

import { Button, Modal, TextInput } from "@mantine/core";
import { MagnifyingGlassIcon, UserIcon } from "@phosphor-icons/react";
import type { User } from "./components/message-content";
import { useChatEncryption } from "@/features/socket/use-chat-encryption";
import { useEffect, useState } from "react";
import { TrashIcon } from "@phosphor-icons/react";
import { StartNewChatModal } from "./start-new-chat-modal";
import { useChatService } from "../patients/hooks/use-chat-service";

interface UserListProps {
  users: User[];
  selectedUserId: string | null;
  onSelectUser: (userId: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  loadMoreRef: React.RefObject<HTMLDivElement | null>;
  isLoadingMore: boolean;
  activeTab: "active" | "closed";
  onTabChange: (tab: "active" | "closed") => void;
  onChatClosed?: (roomId: string) => void;
}

export const UserList: React.FC<UserListProps> = ({
  users,
  selectedUserId,
  onSelectUser,
  searchQuery,
  onSearchChange,
  loadMoreRef,
  isLoadingMore,
  activeTab,
  onTabChange,
  onChatClosed,
}) => {
  const [openNewChat, setOpenNewChat] = useState(false);
  const [deleteUserId, setDeleteUserId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const delteChat = useChatService().closeRoom;
  const { decryptMessage, isEncryptionReady } = useChatEncryption(
    "user-list",
    "room-secret-key",
  );

  const [decryptedMessages, setDecryptedMessages] = useState<
    Record<string, string>
  >({});

  const isValidBase64 = (str: string) => {
    try {
      return btoa(atob(str)) === str;
    } catch {
      return false;
    }
  };

  useEffect(() => {
    if (!selectedUserId && users.length > 0) {
      onSelectUser(users[0].id);
    }
  }, [users, selectedUserId, onSelectUser]);

  useEffect(() => {
    if (!isEncryptionReady || users.length === 0) return;

    let cancelled = false;

    const decryptAllLastMessages = async () => {
      const dec: Record<string, string> = {};

      for (const user of users) {
        const msg = user.lastMessage?.message;

        if (!msg) {
          dec[user.id] = "No messages yet";
          continue;
        }

        if (isValidBase64(msg)) {
          try {
            dec[user.id] = await decryptMessage(msg);
          } catch {
            dec[user.id] = "Encrypted message";
          }
        } else {
          dec[user.id] = msg;
        }
      }

      if (!cancelled) {
        setDecryptedMessages(dec);
      }
    };

    decryptAllLastMessages();

    return () => {
      cancelled = true;
    };
  }, [users, isEncryptionReady]);

  const handleConfirmDelete = async () => {
    if (!deleteUserId) return;
    const roomIdToClose = deleteUserId;

    try {
      setIsDeleting(true);
      delteChat(roomIdToClose, {
        onSuccess: () => {
          // Update local state immediately via parent callback
          onChatClosed?.(roomIdToClose);
        },
      });
    } finally {
      setIsDeleting(false);
      setDeleteUserId(null);
    }
  };

  return (
    <div className="w-full md:max-w-[517.65px] bg-white border border-[#E2E8F0] flex flex-col max-h-[600px]">
      <div className="p-6 space-y-4">
        <div className="flex justify-between items-center ">
          <h2 className="font-poppins font-bold">Conversations</h2>
          <a
            onClick={() => setOpenNewChat(true)}
            className="font-poppins text-xs! cursor-pointer text-[#002FD4]"
          >
            Start New Chat
          </a>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-[#E2E8F0]">
          <button
            onClick={() => onTabChange("active")}
            className={`px-4 py-2 font-poppins font-medium text-sm transition-colors ${
              activeTab === "active"
                ? "text-[#002FD4] border-b-2 border-[#002FD4]"
                : "text-[#64748B] hover:text-[#002FD4]"
            }`}
          >
            Active
          </button>
          <button
            onClick={() => onTabChange("closed")}
            className={`px-4 py-2 font-poppins font-medium text-sm transition-colors ${
              activeTab === "closed"
                ? "text-[#002FD4] border-b-2 border-[#002FD4]"
                : "text-[#64748B] hover:text-[#002FD4]"
            }`}
          >
            Closed
          </button>
        </div>

        <TextInput
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.currentTarget.value)}
          leftSection={<MagnifyingGlassIcon size={16} />}
          radius="md"
          size="md"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {users.map((user) => {
          const displayLastMsg =
            decryptedMessages[user.id] ??
            user.lastMessage?.message ??
            "No messages yet";

          return (
            <div
              key={user.id}
              onClick={() => onSelectUser(user.id)}
              className={`flex items-center gap-3 p-4 cursor-pointer transition-colors ${
                selectedUserId === user.id ? "bg-[#E8EEFD]" : ""
              }`}
            >
              {user.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-[#8a93aeff] flex items-center justify-center">
                  <UserIcon weight="fill" size={24} />
                </div>
              )}

              <div className="flex justify-between w-full min-w-0">
                <div className="min-w-0">
                  <h3 className="font-poppins font-medium text-base">
                    {user.name}
                  </h3>
                  <p className="font-poppins text-sm text-[#64748B] truncate max-w-[280px]">
                    {displayLastMsg}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {user.unread && (
                    <div className="w-7 h-6 bg-[#002FD4] rounded-full flex items-center justify-center text-white text-xs font-semibold">
                      {user.unread_count || 0}
                    </div>
                  )}

                  {/* DELETE BUTTON */}
                  {user.status !== "closed" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteUserId(user.id);
                      }}
                      className="group-hover:opacity-100 transition-opacity text-red-500 hover:text-red-600"
                      aria-label="Delete chat"
                    >
                      <TrashIcon size={18} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        <div
          ref={loadMoreRef}
          className="py-6 text-center text-sm text-gray-500 min-h-[60px]"
        >
          {isLoadingMore
            ? "Loading more conversations..."
            : users.length === 0
              ? "No conversations found"
              : ""}
        </div>
      </div>
      <StartNewChatModal
        opened={openNewChat}
        onClose={() => setOpenNewChat(false)}
        onSelectPatient={(patientId) => {
          onSelectUser(patientId);
          setOpenNewChat(false);
        }}
      />
      <Modal
        opened={!!deleteUserId}
        onClose={() => setDeleteUserId(null)}
        title="Delete Conversation"
        centered
      >
        <div className="space-y-4 mt-3">
          <p className="text-sm text-gray-600">
            Are you sure you want to delete this conversation? This action
            cannot be undone.
          </p>

          <div className="flex justify-between gap-3">
            <Button
              variant="default"
              onClick={() => setDeleteUserId(null)}
              disabled={isDeleting}
            >
              Cancel
            </Button>

            <Button
              color="red"
              loading={isDeleting}
              onClick={handleConfirmDelete}
            >
              End Conversation
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
