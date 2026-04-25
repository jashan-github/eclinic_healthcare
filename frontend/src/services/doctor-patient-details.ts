// src/services/doctor-patient-details.ts
import api from '@/lib/api'

export interface PatientDetailsResponse {
  id: string
  name: string
  age: {
    age: number
    type: string
    full_age: string
  }
  phone_number: string
  gender: string
  address: string | null
  email: string
  emergency_contact_number: string | null
  blood_type: string | null
  occupation: string | null
  date_of_birth: string
  family_contact_number: string | null
  marital_status: string | null
  preferred_language: string | null
  health_issues: string[]
}

export interface PatientDetailsData {
  status: boolean
  data: PatientDetailsResponse
}

export const fetchPatientDetails = async (patientId: string): Promise<PatientDetailsResponse> => {
  try {
    const response = await api.get<PatientDetailsData>(`/doctor/patients/${patientId}`)
    return response.data.data
  } catch (error) {
    console.error(`Failed to fetch patient details for ID: ${patientId}`, error)
    throw new Error('Unable to load patient details')
  }
}