import api from '@/lib/api'

// Doctor's Patients List
export interface DoctorPatient {
  id: string
  name: string
  email: string
  phone: string
  age?: number
  gender?: string
  last_visit_date?: string
  total_visits?: number
  has_medical_history?: boolean
  created_at: string
  updated_at: string
}

export interface DoctorPatientsResponse {
  success: boolean
  message: string
  data: {
    patients: DoctorPatient[]
    total: number
    page?: number
    limit?: number
  }
}

/**
 * Get doctor's patients list
 * GET /api/v1/doctor/patients
 */
export const fetchDoctorPatients = async (): Promise<DoctorPatientsResponse> => {
  try {
    const response = await api.get<DoctorPatientsResponse>('/v1/doctor/patients')
    console.log('📡 Doctor patients response:', response.data)
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch doctor patients:', error)
    throw new Error(error.response?.data?.message || 'Failed to load patients list')
  }
}

// Patient Detailed Information
export interface PatientDetails {
  id: string
  name: string
  email: string
  phone: string
  date_of_birth?: string
  age?: number
  gender?: string
  address?: string
  city?: string
  state?: string
  country?: string
  zip_code?: string
  emergency_contact_name?: string
  emergency_contact_phone?: string
  blood_group?: string
  allergies?: string[]
  last_visit_date?: string
  total_visits?: number
  created_at: string
  updated_at: string
}

export interface PatientDetailsResponse {
  success: boolean
  message: string
  data: {
    patient: PatientDetails
  }
}

/**
 * Get patient's detailed information
 * GET /api/v1/doctor/patients/{patient_id}
 */
export const fetchPatientDetails = async (patientId: string): Promise<PatientDetailsResponse> => {
  try {
    const response = await api.get<PatientDetailsResponse>(`/v1/doctor/patients/${patientId}`)
    console.log('📡 Patient details response:', response.data)
    return response.data
  } catch (error: any) {
    console.error(`Failed to fetch patient details for: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to load patient details')
  }
}

// Patient Medical Information
export interface PatientMedicalInfo {
  id: string
  patient_id: string
  blood_group?: string
  height?: number
  weight?: number
  bmi?: number
  allergies?: string[]
  chronic_conditions?: string[]
  current_medications?: Array<{
    name: string
    dosage: string
    frequency: string
  }>
  past_surgeries?: Array<{
    surgery: string
    date: string
    notes?: string
  }>
  family_history?: string[]
  smoking_status?: 'never' | 'former' | 'current'
  alcohol_consumption?: 'never' | 'occasional' | 'regular'
  exercise_frequency?: string
  diet_preferences?: string
  immunizations?: Array<{
    vaccine: string
    date: string
  }>
  notes?: string
  created_at: string
  updated_at: string
}

export interface PatientMedicalResponse {
  success: boolean
  message: string
  data: {
    medical_info: PatientMedicalInfo
  }
}

/**
 * Get patient's medical information
 * GET /api/v1/doctor/patients/{patient_id}/medical
 */
export const fetchPatientMedicalInfo = async (patientId: string): Promise<PatientMedicalResponse> => {
  try {
    const response = await api.get<PatientMedicalResponse>(`/v1/doctor/patients/${patientId}/medical`)
    console.log('📡 Patient medical info response:', response.data)
    return response.data
  } catch (error: any) {
    console.error(`Failed to fetch medical info for patient: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to load patient medical information')
  }
}

/**
 * Update patient's medical information
 * PUT /api/v1/doctor/patients/{patient_id}/medical
 */
export const updatePatientMedicalInfo = async (
  patientId: string,
  medicalData: Partial<PatientMedicalInfo>
): Promise<PatientMedicalResponse> => {
  try {
    const response = await api.put<PatientMedicalResponse>(
      `/v1/doctor/patients/${patientId}/medical`,
      medicalData
    )
    console.log('📡 Update medical info response:', response.data)
    return response.data
  } catch (error: any) {
    console.error(`Failed to update medical info for patient: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to update patient medical information')
  }
}

