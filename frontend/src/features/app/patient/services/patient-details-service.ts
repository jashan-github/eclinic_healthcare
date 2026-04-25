// src/services/patient-details-service.ts

import api from '@/lib/api'

export interface PatientAge {
  age: number
  type: string
  full_age: string
}

export interface PatientDetails {
  id: string
  name: string
  age: PatientAge
  phone_number: string
  gender: string
  address: string
  email: string
  emergency_contact_number: string
  blood_type: string
  occupation: string
  date_of_birth: string
  family_contact_number: string
  marital_status: string
  preferred_language: string
  health_issues: string[]
  today_appointment_id?: string
}

export interface PatientDetailsResponse {
  success: boolean
  data: PatientDetails
  errors: Record<string, any>
}

export const fetchPatientDetails = async (patientId: string): Promise<PatientDetails> => {
  try {
    const response = await api.get<PatientDetailsResponse>(
      `/v1/doctor/patients/${patientId}`
    )
    console.log('📡 Patient overview response:', response.data)
    return response.data.data
  } catch (error: any) {
    console.error(`Failed to fetch patient details for ID: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to load patient details')
  }
}