// src/services/appointment-request-services.ts
import api from '@/lib/api'

export interface Patient {
  id: string
  name: string
  email: string
  phone: string | null
  gender: string
  desc: string
  age: number
}

export interface Service {
  id: string
  name: string
}

export interface AppointmentRequestNew {
  id: string
  patient_id: string
  patient: Patient
  service_id: string
  service: Service
  doctor_id: string
  clinic_id: string
  description: string
  preferred_date: string
  preferred_time: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  duration_minutes: number
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED'
  price_amount: number
  currency: string
  created_at: string
  updated_at: string
}

export interface PaginationInfo {
  current_page: number
  per_page: number
  total: number
  total_pages: number
}

export interface AppointmentRequestsAPIResponse {
  success: boolean
  message: string
  data: {
    requests: AppointmentRequestNew[]
    pagination: PaginationInfo
  }
  errors: any
}

// Transformed response for frontend use
export interface AppointmentRequestsResponse {
  total: number
  requests: AppointmentRequestNew[]
  pagination: PaginationInfo
}

// Legacy types for backward compatibility
export interface PatientDetails {
  id: string
  name: string
  gender: string
  age: number
  avatar_url?: any
}

export interface AppointmentRequest {
  id: string
  patient_details: PatientDetails
  consultation_type: 'In-Clinic' | 'Teleconsultation'
  reason_summary: string
  reason_detailed: string
  requested_appointment_date_time: string
  submitted_date_time: string
  status: 'pending' | 'processed'
  actions: {
    can_approve: boolean
    can_decline: boolean
  }
}

// Fetch pending requests using new API
export const fetchPendingRequests = async (
  page = 1,
  limit = 20,
  search?: string
): Promise<AppointmentRequestsResponse> => {
  try {
    const params: Record<string, any> = {
      status: 'PENDING',
      page,
      limit,
    }

    if (search) params.search = search

    const response = await api.get<AppointmentRequestsAPIResponse>(
      '/v1/appointment/requests',
      { params }
    )

    return {
      total: response.data.data.pagination.total,
      requests: response.data.data.requests,
      pagination: response.data.data.pagination,
    }
  } catch (error) {
    console.error('Failed to fetch pending requests:', error)
    throw new Error('Unable to load pending requests')
  }
}

// Fetch processed (accepted) requests using new API
export const fetchProcessedRequests = async (
  page = 1,
  limit = 20,
  search?: string
): Promise<AppointmentRequestsResponse> => {
  try {
    const params: Record<string, any> = {
      status: 'ACCEPTED',
      page,
      limit,
    }

    if (search) params.search = search

    const response = await api.get<AppointmentRequestsAPIResponse>(
      '/v1/appointment/requests',
      { params }
    )

    return {
      total: response.data.data.pagination.total,
      requests: response.data.data.requests,
      pagination: response.data.data.pagination,
    }
  } catch (error) {
    console.error('Failed to fetch processed requests:', error)
    throw new Error('Unable to load processed requests')
  }
}