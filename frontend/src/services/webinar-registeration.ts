// src/services/webinar-registeration.ts
import api from '@/lib/api'

export interface RegisterWebinarPayload {
  webinar_id: string
}

export interface RegisterWebinarResponse {
  success: boolean
  message: string
  data?: any
}

// Register for webinar
export const registerForWebinar = async (payload: RegisterWebinarPayload): Promise<RegisterWebinarResponse> => {
  try {
    const response = await api.post<RegisterWebinarResponse>('/v1/patient/webinars/register', payload)
    return response.data
  } catch (error: any) {
    console.error('Failed to register for webinar:', error)
    const message = 
      error?.response?.data?.message ||
      error?.message ||
      'Failed to register for webinar'
    throw new Error(message)
  }
}
