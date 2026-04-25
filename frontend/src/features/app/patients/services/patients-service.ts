// src/services/patients-service.ts
import axiosInstance from '@/lib/api'

export interface PatientsResponse {
  success: boolean
  message: string
  data: {
    patients: Patient[]
    pagination: {
      total: number
      page: number
      per_page: number
      total_pages: number
    }
  }
  errors: any | null
}

export interface Medication {
  name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
}

export interface CustomCondition {
  name: string;
  years?: number;
}

export interface MedicalInfo {
  smoke_years?: number;
  alcohol_years?: number;
  hypertension_years?: number;
  diabetes_mellitus_years?: number;
  hypothyroidism_years?: number;
  existing_condition?: string;
  existing_condition_years?: number;
  current_medications?: Medication[];
  custom_conditions?: CustomCondition[];
}

export interface Patient {
  id: string
  name: string
  email?: string
  phone?: string
  age: number
  gender: string
  clinic_id: string
  clinic_name: string
  is_active: boolean
  last_visited_date?: string
  medical_history_text?: string
  total_appointments: number
  has_medical_history: boolean
  available_actions: string[]
  is_appointment_request?: boolean
  chat_room_id?: string | null
  today_appointment_id?: string
  medical_info?: MedicalInfo;
}

export const getAllPatients = async (page: number = 1, perPage: number = 20): Promise<PatientsResponse['data']> => {
  try {
    const { data } = await axiosInstance.get(`/v1/doctor/patients`, {
      params: {
        page,
        per_page: perPage,
      },
    })

    if (!data.success) {
      throw new Error(data.message || 'Failed to fetch patients')
    }
    return data.data
  } catch (error) {
    console.error('Error fetching patients:', error)
    throw error
  }
}

export const generateUHIDForNewPatient = async () => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/patients/generate-uhid')
    return data.data
  } catch (error) {
    console.error(error)
    throw error
  }
}