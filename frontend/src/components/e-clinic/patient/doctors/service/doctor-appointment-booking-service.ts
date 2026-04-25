// src/services/appointment-request-service.ts
import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'

export interface AppointmentRequestPayload {
  doctor_id: string
  service_id: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  preferred_date: string // YYYY-MM-DD
  preferred_time: string // HH:MM:SS (24-hour)
  reason: string
}

export interface AppointmentRequestResponse {
  // Assume generic success response from backend
  appointment_id?: string
  status?: string
  message?: string
  // Add more if you know exact response later
}

export const requestAppointment = async (
  payload: AppointmentRequestPayload
): Promise<AppointmentRequestResponse> => {
  try {
    const { data } = await axiosInstance.post<ApiResponse<AppointmentRequestResponse>>(
      '/v1/patient/appointments/request',
      payload
    )

    return data.data || { message: data.message || 'Appointment requested successfully' }
  } catch (error) {
    console.error('Failed to request appointment:', error)
    throw error
  }
}