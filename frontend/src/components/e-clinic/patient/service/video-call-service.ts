// src/services/video-call-service.ts
import api from '@/lib/api-webinars'

// Types based on your curl example + reasonable assumptions
export interface CreateVideoSessionRequest {
  appointment_id: string
  recording_enabled: boolean
  scheduled_start_time: string      // ISO 8601 format
  scheduled_end_time: string        // ISO 8601 format
  session_type: 'appointment' | 'webinar' | 'consultation' // adjust enum as needed
}

export interface VideoSessionResponse {
  success: boolean
  message: string
  data: {
    session_id: string
    appointment_id: string
    join_url: string                // for patient/doctor
    host_url?: string               // optional - if separate host link
    recording_enabled: boolean
    scheduled_start_time: string
    scheduled_end_time: string
    status: 'SCHEDULED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED'
    created_at: string
    // optional - depending on your backend
    meeting_password?: string
    provider?: 'zoom' | 'agora' | 'whereby' | 'custom'
  }
  errors: any | null
}

export interface VideoSessionStatusResponse {
  success: boolean
  message: string
  data: {
    session_id: string
    status: 'SCHEDULED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED'
    is_active: boolean
    join_url: string | null
    recording_url?: string | null
  }
  errors: any | null
}

// Create a new video session
export const createVideoSession = async (
  payload: CreateVideoSessionRequest
): Promise<VideoSessionResponse> => {
  const response = await api.post('/v1/video-sessions', payload)
  return response.data
}

// Optional: Get status/info of a video session
export const getVideoSessionStatus = async (
  sessionId: string
): Promise<VideoSessionStatusResponse> => {
  const response = await api.get(`/v1/video-sessions/${sessionId}/status`)
  return response.data
}

// Optional: Get join info (can be same as status or separate endpoint)
export const getVideoSessionJoinInfo = async (
  sessionId: string
): Promise<VideoSessionResponse> => {
  const response = await api.get(`/v1/video-sessions/${sessionId}`)
  return response.data
}