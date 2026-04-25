import api from '@/lib/api'

export interface PatientListItem {
  id: string
  name: string
  email: string
  phone: string | null
  gender: string
  age: number
  clinic_id: string
  clinic_name: string
  is_active: boolean
  last_visited_date: string
  total_appointments: number
  has_medical_history: boolean
  has_vital_signs_shared: boolean
  medical_history_text: string
  available_actions: string[]
  today_appointment_id: string | null
}

export interface PatientsListResponse {
  success: boolean
  message: string
  data: {
    patients: PatientListItem[]
    pagination: {
      total: number
      page: number
      per_page: number
      total_pages: number
    }
  }
  errors: null | any
}

export const fetchDoctorPatientsList = async (params?: {
  page?: number
  per_page?: number
}): Promise<PatientsListResponse> => {
  const { data } = await api.get<PatientsListResponse>('/v1/doctor/patients', {
    params: {
      page: params?.page || 1,
      per_page: params?.per_page || 100 // Fetch more to find the patient
    }
  })
  return data
}

