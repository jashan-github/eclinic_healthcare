// src/services/video-call-service.ts
import api from '@/lib/api-webinars'

// Create Payload & Response
export interface CreateVideoSessionPayload {
  appointment_id?: string
  webinar_id?: string
  session_type: 'appointment' | 'webinar'
  scheduled_start_time: string // ISO 8601
  scheduled_end_time: string // ISO 8601
  recording_enabled: boolean
}

export interface VideoSession {
  id?: string
  session_id?: string
  session_type: 'appointment' | 'webinar'
  appointment_id?: string
  webinar_id?: string
  channel_name: string
  agora_token?: string
  status: 'scheduled' | 'CREATED' | 'JOINING' | 'ACTIVE' | 'GRACE' | 'COMPLETED' | 'JOIN_FAILED'
  scheduled_start_time?: string
  scheduled_end_time?: string
  actual_start_time?: string
  actual_end_time?: string
  recording_enabled?: boolean
  billable_duration_minutes?: number
  created_at?: string
  updated_at?: string
}

export interface BaseResponse<T> {
  success: boolean
  message: string
  data: T
  errors: any | null
}

// Create session
export const createVideoSession = async (payload: CreateVideoSessionPayload): Promise<BaseResponse<VideoSession>> => {
  const response = await api.post('/v1/video-sessions', payload)
  return response.data
}

export interface JoinResponse {
  status: string
  token: string | null
  channel_name: string
  waiting_room: boolean
  message?: string
  doctor_ready: boolean
  patient_ready: boolean
  both_ready: boolean
  watchdog_expires_at?: string
  join_data?: {
    type: string
    session_id: string
    channel_name: string
    doctor_token: string
    patient_token: string
    watchdog_expires_at: string
    status: string
    message: string
  }
}

export const joinVideoSession = async (sessionId: string): Promise<BaseResponse<JoinResponse>> => {
  const response = await api.post(`/v1/video-sessions/${sessionId}/join`)
  return response.data
}

// Join success (POST /v1/video-sessions/{session_id}/join-success)
export const confirmJoinSuccess = async (sessionId: string): Promise<BaseResponse<VideoSession>> => {
  const response = await api.post(`/v1/video-sessions/${sessionId}/join-success`)
  return response.data
}

// Join failure (POST /v1/video-sessions/{session_id}/join-failure)
export const reportJoinFailure = async (sessionId: string): Promise<BaseResponse<VideoSession>> => {
  const response = await api.post(`/v1/video-sessions/${sessionId}/join-failure?error=error&error_code=JOIN_FAILED`)
  return response.data
}

// Waiting room status (GET /v1/video-sessions/{session_id}/waiting-room)
export interface WaitingRoomResponse {
  status: string
  waiting_room: boolean
  doctor_ready: boolean
  patient_ready: boolean
  both_ready: boolean
  app_id: string
  token: string | null
  channel_name: string
  message?: string
  watchdog_expires_at?: string
}

export const getWaitingRoomStatus = async (sessionId: string): Promise<BaseResponse<WaitingRoomResponse>> => {
  const response = await api.get(`/v1/video-sessions/${sessionId}/waiting-room`)
  return response.data
}

// Session status (GET /v1/video-sessions/{session_id}/status)
export const getVideoSessionStatus = async (sessionId: string): Promise<BaseResponse<VideoSession>> => {
  const response = await api.get(`/v1/video-sessions/${sessionId}/status`)
  return response.data
}

// Retry session (POST /v1/video-sessions/retry) - assuming payload if needed, else empty
export const retryVideoSession = async (): Promise<BaseResponse<VideoSession>> => {
  const response = await api.post('/v1/video-sessions/retry')
  return response.data
}

// End session (POST /v1/video-sessions/{session_id}/end)
export const endVideoSession = async (sessionId: string): Promise<BaseResponse<VideoSession>> => {
  const response = await api.post(`/v1/video-sessions/${sessionId}/end`)
  return response.data
}

// Leave channel (POST /v1/video-sessions/{session_id}/leave-channel)
export const leaveChannel = async (sessionId: string): Promise<BaseResponse<any>> => {
  const response = await api.post(`/v1/video-sessions/${sessionId}/leave-channel`)
  return response.data
}