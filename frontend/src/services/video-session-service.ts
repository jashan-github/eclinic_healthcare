import api from '@/lib/api'

// Types
export interface CreateVideoSessionPayload {
  appointment_id?: string
  webinar_id?: string
  session_type: 'appointment' | 'webinar'
  scheduled_start_time: string // ISO 8601 format
  scheduled_end_time: string // ISO 8601 format
  recording_enabled: boolean
}

export interface VideoSession {
  id?: string
  session_id?: string // Backend returns session_id instead of id
  session_type: 'appointment' | 'webinar'
  appointment_id?: string
  webinar_id?: string
  channel_name: string
  agora_token?: string // Token might not be in create response, comes from join API
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

export interface JoinSessionResponse {
  token: string
  channel_name: string
  status: 'TOKEN_ISSUED' | 'WAITING_ROOM'
  message?: string
}

export interface WaitingRoomStatus {
  status: 'WAITING' | 'READY' | 'DOCTOR_NOT_JOINED'
  token?: string
  channel_name?: string
  message?: string
}

export interface RetrySessionPayload {
  previous_session_id: string
}

// API Functions

/**
 * Create a new video session
 * HIPAA Compliance:
 * - Channel name is secure hash (no PHI)
 * - Tokens generated server-side only
 * - Full audit logging
 */
export const createVideoSession = async (payload: CreateVideoSessionPayload): Promise<VideoSession> => {
  const response = await api.post<{ success: boolean; data: VideoSession }>('/v1/video-sessions', payload)
  console.log('📡 Create video session response:', response.data)
  const data = response.data.data
  
  // Backend returns session_id, normalize to id for consistency
  if (data.session_id && !data.id) {
    data.id = data.session_id
  }
  
  console.log('📦 Normalized session data:', data)
  return data
}

/**
 * Request to join a video session
 * Doctor: Can join 5-10 min early, gets token immediately, 30s watchdog starts
 * Patient: Enters waiting room if doctor not joined, gets token when doctor joins
 * 
 * Security:
 * - Tokens generated server-side only
 * - 30-second join watchdog enforced
 * - Full audit logging
 */
export const joinVideoSession = async (sessionId: string, userId?: string, role?: string): Promise<JoinSessionResponse> => {
  console.log('📡 Calling join video session API:', `/v1/video-sessions/${sessionId}/join`)
  
  // Backend might need user info in request body
  const requestBody = {
    user_id: userId,
    role: role || 'host'
  }
  
  console.log('📡 Join request body:', requestBody)
  
  const response = await api.post<{ success: boolean; data: JoinSessionResponse }>(
    `/v1/video-sessions/${sessionId}/join`,
    requestBody
  )
  console.log('📡 Join video session response:', response.data)
  return response.data.data
}

/**
 * Confirm successful join (called when Agora reports join success)
 * 
 * Critical for Billing:
 * - Billing starts when doctor confirms join success
 * - Patient gets token notification when doctor joins
 */
export const confirmJoinSuccess = async (sessionId: string): Promise<void> => {
  await api.post(`/v1/video-sessions/${sessionId}/join-success`)
}

/**
 * Report join failure (called when Agora reports failure or timeout)
 * 
 * Behavior:
 * - If in JOINING state, transitions to JOIN_FAILED
 * - 30-second watchdog also triggers this automatically
 * - Tokens are revoked
 * - No billing occurs
 */
export const reportJoinFailure = async (
  sessionId: string,
  error: string,
  errorCode: string = 'JOIN_FAILED'
): Promise<void> => {
  await api.post(`/v1/video-sessions/${sessionId}/join-failure`, null, {
    params: { error, error_code: errorCode }
  })
}

/**
 * Get waiting room status for patient
 * Returns current status and token if doctor has joined
 */
export const getWaitingRoomStatus = async (sessionId: string): Promise<WaitingRoomStatus> => {
  const response = await api.get<{ success: boolean; data: WaitingRoomStatus }>(
    `/v1/video-sessions/${sessionId}/waiting-room`
  )
  return response.data.data
}

/**
 * Retry a failed call by creating new session instance
 * 
 * Critical:
 * - Creates NEW session with NEW channel and NEW tokens
 * - Previous session is marked as failed
 * - Retry count is incremented
 */
export const retryVideoSession = async (payload: RetrySessionPayload): Promise<VideoSession> => {
  const response = await api.post<{ success: boolean; data: VideoSession }>('/v1/video-sessions/retry', payload)
  return response.data.data
}

/**
 * End a video call
 * - Transitions to GRACE period, then COMPLETED
 * - Calculates final billable duration
 */
export const endVideoSession = async (sessionId: string): Promise<void> => {
  await api.post(`/v1/video-sessions/${sessionId}/end`)
}

