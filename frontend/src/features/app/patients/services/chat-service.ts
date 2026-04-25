// src/services/chat-service.ts
import axiosInstance from "@/lib/api-chat";

export interface CreatePrivateChatResponse {
  room_id: string;
  doctor_id: string;
  patient_id: string;
  appointment_id: string | null;
  status: string;
  created_at: string;
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

export const getAllChats = async (limit = 50, offset = 0) => {
  try {
    const { data } = await axiosInstance.get(
      `/api/chat/rooms?limit=${limit}&offset=${offset}`,
    );
    return data;
  } catch (error: any) {
    console.error("Error fetching chats:", error);
    throw error.response?.data || error;
  }
};

export const getActiveChats = async (limit = 50, offset = 0) => {
  try {
    const { data } = await axiosInstance.get(
      `/api/chat/rooms/active?limit=${limit}&offset=${offset}`,
    );
    return data;
  } catch (error: any) {
    console.error("Error fetching active chats:", error);
    throw error.response?.data || error;
  }
};

export const getClosedChats = async (limit = 50, offset = 0) => {
  try {
    const { data } = await axiosInstance.get(
      `/api/chat/rooms/closed?limit=${limit}&offset=${offset}`,
    );
    return data;
  } catch (error: any) {
    console.error("Error fetching closed chats:", error);
    throw error.response?.data || error;
  }
};

export const createPrivateChat = async (
  patientId: string,
): Promise<CreatePrivateChatResponse> => {
  try {
    const response = await axiosInstance.post("/api/chat/start", {
      patient_id: patientId,
    });

    return response.data;
  } catch (error: any) {
    console.error(`Failed to start chat with patient ${patientId}:`, error);

    const errorMessage =
      error?.response?.data?.message ||
      error?.message ||
      "Failed to start chat";
    throw new Error(errorMessage);
  }
};
export const closeChatRoom = async (
  roomId: string,
): Promise<CreatePrivateChatResponse> => {
  try {
    const response = await axiosInstance.post(`/api/chat/${roomId}/close`);

    return response.data;
  } catch (error: any) {
    const errorMessage =
      error?.response?.data?.message ||
      error?.message ||
      "Failed to start chat";
    throw new Error(errorMessage);
  }
};

export const getChatMessages = async (
  roomId: string,
  limit = 100,
  offset = 0,
): Promise<MessagesResponse> => {
  try {
    const { data } = await axiosInstance.get(
      `/api/chat/${roomId}/messages?limit=${limit}&offset=${offset}`,
    );
    return data;
  } catch (error: any) {
    console.error(`Error fetching messages for room ${roomId}:`, error);
    throw error.response?.data || error;
  }
};
