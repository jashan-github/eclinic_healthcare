import api from '@/lib/api'

// ==================== Interfaces ====================

export interface StaffAppointmentItem {
  id: string
  patient_id: string
  patient_name: string
  patient_email?: string
  patient_phone?: string
  patient_profile_image?: string
  patient_gender?: string
  patient_age?: number
  service_id: string
  service_name?: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  appointment_date: string
  start_time: string
  end_time?: string
  status: 'CONFIRMED' | 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'
  price_amount?: number
  currency?: string
  duration_minutes: number
  payment_status?: string
  payment_type?: string
  payment_method?: string
  doctor_id?: string
  doctor_name?: string
  emergency_contact?: string
  family_contact?: string
}

export interface PaginationInfo {
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface DoctorProfile {
  id: string
  user_id: string
  first_name: string
  middle_name: string | null
  last_name: string
  date_of_birth: string
  age: number
  phone_number: string
  email: string
  education: string
  years_of_experience: number
  languages: Array<{
    id: string
    language_name: string
    language_code: string
  }>
  specializations: Array<{
    id: string
    name: string
    image: string
  }>
  about: string
  profile_img: string
  created_at: string
  updated_at: string
}

export interface StaffAppointmentsResponse {
  success: boolean
  message: string
  data: {
    doctor_profile: DoctorProfile
    appointments: StaffAppointmentItem[]
    pagination: PaginationInfo
  }
  errors: any
}

export interface StaffAppointmentsParams {
  type?: 'today' | 'upcoming'
  search?: string
  page?: number
  per_page?: number
}

export interface PatientContactDetails {
  full_name: string
  email: string
  contact: string
  emergency_contact: string | null
  family_contact: string | null
}

export interface PatientContactDetailsResponse {
  success: boolean
  message: string
  data: PatientContactDetails
  errors: any
}

export interface StaffStatsData {
  today_appointments_count: number
  active_patients_count: number
  pending_appointment_requests_count: number
}

export interface StaffStatsResponse {
  success: boolean
  message: string
  data: StaffStatsData
  errors: any
}

export interface StaffPatientItem {
  id: string
  name: string
  email: string
  contact?: string | null
  gender: string
  age: number
  emergency_contact?: string | null
  family_contact?: string | null
  profile_image?: string | null
  [key: string]: any
}

export interface StaffPatientsResponse {
  success: boolean
  message: string
  data: {
    patients: StaffPatientItem[]
    pagination: PaginationInfo
  }
  errors: any
}

export interface StaffPatientsParams {
  page?: number
  per_page?: number
  search?: string
}

export interface StaffInvoiceItem {
  id: string
  invoice_number: string
  patient_id: string
  patient_name: string
  patient_email?: string
  patient_phone?: string
  appointment_id: string
  service_name?: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  appointment_date: string
  appointment_time?: string
  amount: number
  currency: string
  payment_status: 'paid' | 'pending' | 'failed' | 'processing'
  payment_method?: 'online' | 'cash'
  payment_date?: string
  created_at: string
  updated_at: string
}

export interface StaffInvoicesResponse {
  success: boolean
  message: string
  data: {
    invoices: StaffInvoiceItem[]
    pagination: PaginationInfo
  }
  errors: any | null
}

export interface StaffInvoicesParams {
  page?: number
  per_page?: number
  search?: string
  payment_method?: 'online' | 'cash'
  payment_status?: 'paid' | 'pending' | 'failed' | 'processing'
}

// ==================== Service Functions ====================

/**
 * Fetch appointments for the assigned doctor
 */
export const fetchStaffAssignedDoctorAppointments = async (
  params?: StaffAppointmentsParams
): Promise<StaffAppointmentsResponse> => {
  try {
    const queryParams: Record<string, string> = {}
    
    if (params?.type) {
      queryParams.type = params.type
    }
    if (params?.search) {
      queryParams.search = params.search
    }
    if (params?.page) {
      queryParams.page = String(params.page)
    }
    if (params?.per_page) {
      queryParams.per_page = String(params.per_page)
    }

    const response = await api.get<StaffAppointmentsResponse>(
      '/v1/staff/assigned-doctor',
      { params: queryParams }
    )
    
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch staff assigned doctor appointments:', error)
    throw new Error(error.response?.data?.message || 'Unable to load appointments')
  }
}

/**
 * Fetch patient contact details
 */
export const fetchPatientContactDetails = async (
  patientId: string
): Promise<PatientContactDetailsResponse> => {
  try {
    const response = await api.get<PatientContactDetailsResponse>(
      `/v1/staff/patients/${patientId}/contact-details`
    )
    
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch patient contact details:', error)
    throw new Error(error.response?.data?.message || 'Unable to load contact details')
  }
}

/**
 * Fetch staff dashboard statistics
 */
export const fetchStaffStats = async (): Promise<StaffStatsResponse> => {
  try {
    const response = await api.get<StaffStatsResponse>('/v1/staff/stats')
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch staff stats:', error)
    throw new Error(error.response?.data?.message || 'Unable to load dashboard statistics')
  }
}

/**
 * Fetch staff patients list
 */
export const fetchStaffPatients = async (
  params?: StaffPatientsParams
): Promise<StaffPatientsResponse> => {
  try {
    const queryParams: Record<string, string> = {}
    
    if (params?.page) {
      queryParams.page = String(params.page)
    }
    if (params?.per_page) {
      queryParams.per_page = String(params.per_page)
    }
    if (params?.search) {
      queryParams.search = params.search
    }

    const response = await api.get<StaffPatientsResponse>(
      '/v1/staff/patients',
      { params: queryParams }
    )
    
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch staff patients:', error)
    throw new Error(error.response?.data?.message || 'Unable to load patients')
  }
}

/**
 * Fetch staff invoices list
 */
export const fetchStaffInvoices = async (
  params?: StaffInvoicesParams
): Promise<StaffInvoicesResponse> => {
  try {
    const queryParams: Record<string, string> = {}
    
    if (params?.page) {
      queryParams.page = String(params.page)
    }
    if (params?.per_page) {
      queryParams.per_page = String(params.per_page)
    }
    if (params?.search) {
      queryParams.search = params.search
    }
    if (params?.payment_method) {
      queryParams.payment_method = params.payment_method
    }
    if (params?.payment_status) {
      queryParams.payment_status = params.payment_status
    }

    const response = await api.get<StaffInvoicesResponse>(
      '/v1/staff/invoices',
      { params: queryParams }
    )
    
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch staff invoices:', error)
    throw new Error(error.response?.data?.message || 'Unable to load invoices')
  }
}

/**
 * Download invoice receipt
 */
export const downloadStaffInvoice = async (invoiceId: string): Promise<Blob> => {
  try {
    const response = await api.get(
      `/v1/staff/invoices/${invoiceId}/download`,
      { responseType: 'blob' }
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to download invoice:', error)
    throw new Error(error.response?.data?.message || 'Unable to download invoice')
  }
}

