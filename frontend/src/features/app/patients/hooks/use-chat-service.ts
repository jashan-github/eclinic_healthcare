import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "react-toastify";
import {
  closeChatRoom,
  createPrivateChat,
  getAllChats,
  getChatMessages,
  type CreatePrivateChatResponse,
} from "../services/chat-service";

interface Chat {
  id: string;
  name: string;
  type: string;
  avatar: string | null;
  last_message_at?: string;
  unread_count?: number;
  last_message?: {
    id: string;
    message: string;
    sender_id: string;
    sender_type: string;
    message_type: string;
    created_at: string;
  };
}

interface ChatsResponse {
  rooms: Chat[];
  total: number;
}

export interface ChatMessage {
  id: string;
  chat_room_id: string;
  sender_id: string;
  sender_type: string;
  message_type: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export interface MessagesResponse {
  messages: ChatMessage[];
  total: number;
  room_id: string;
}

export const useChatService = (
  fetchList: boolean = false,
  page = 1,
  perPage = 15,
) => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const limit = perPage;
  const offset = (page - 1) * perPage;

  const {
    data: chatsData,
    isLoading: isLoadingChats,
    isError: isChatsError,
    refetch: refetchChats,
  } = useQuery<ChatsResponse>({
    queryKey: ["chats", page, perPage],
    queryFn: () => getAllChats(limit, offset),
    staleTime: 1000 * 60 * 2,
    enabled: fetchList,
  });

  const createChatMutation = useMutation({
    mutationFn: (patientId: string) => createPrivateChat(patientId),

    onSuccess: (data: CreatePrivateChatResponse) => {
      const chatId = data.room_id;
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      toast.success("Chat started!");
      navigate({ to: `/app/messages/${chatId}` });
    },

    onError: (error: any) => {
      if (error?.message === "Request failed with status code 403") {
        toast.error("Only doctors can start chat");
      } else {
        toast.error("Failed to start chat");
      }
    },
  });

  const useRoomMessages = (roomId: string | null) => {
    return useQuery<MessagesResponse>({
      queryKey: ["chat-messages", roomId],
      queryFn: () => getChatMessages(roomId!, 100, 0),
      enabled: !!roomId,
      staleTime: 1000 * 30, // 30 seconds
      gcTime: 1000 * 60 * 5, // 5 minutes cache
    });
  };

  const closeRoom = useMutation({
    mutationFn: (roomId: string) => closeChatRoom(roomId),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      toast.success("Delted Successfully");
    },

    onError: (error: any) => {
      toast.error(error?.response?.data?.message);
    },
  });

  return {
    chats: chatsData?.rooms || [],
    total: chatsData?.total || 0,

    isLoadingChats,
    isChatsError,

    createChat: createChatMutation.mutate,
    closeRoom: closeRoom.mutate,
    createChatAsync: createChatMutation.mutateAsync,
    isCreatingChat: createChatMutation.isPending,

    refetchChats,

    useRoomMessages,
  };
};
