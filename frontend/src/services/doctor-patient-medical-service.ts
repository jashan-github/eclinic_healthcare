import api from '@/lib/api'

// Interface for custom condition
export interface CustomCondition {
  name: string
  years: number | null
}

// Interface for current medication
export interface CurrentMedication {
  name: string
  dosage: string
  frequency: string
}

// Interface for medical info structure
export interface MedicalInfo {
  diabetes_mellitus_years: number | null
  hypertension_years: number | null
  hypothyroidism_years: number | null
  alcohol_years: number | null
  tobacco_years: number | null
  smoke_years: number | null
  custom_conditions: CustomCondition[]
  existing_condition: string | null
  existing_condition_years: number | null
  allergies: string | null
  allergies_years: number | null
  current_medications: CurrentMedication[]
}

// Interface for patient medical information response
export interface PatientMedicalInfoResponse {
  success: boolean
  message: string
  data: {
    patient_id?: string
    medical_info: MedicalInfo
  }
  errors: null | any
}

// Interface for updating patient medical information
export interface UpdatePatientMedicalPayload {
  medical_info: MedicalInfo
}

// GET: Fetch patient's medical information
export const getPatientMedicalInfo = async (
  patientId: string
): Promise<PatientMedicalInfoResponse> => {
  try {
    const response = await api.get<PatientMedicalInfoResponse>(
      `/v1/doctor/patients/${patientId}/medical`
    )
    return response.data
  } catch (error) {
    console.error('Failed to fetch patient medical information:', error)
    throw error
  }
}

// PUT: Update patient's medical information
export const updatePatientMedicalInfo = async (
  patientId: string,
  payload: UpdatePatientMedicalPayload
): Promise<PatientMedicalInfoResponse> => {
  try {
    const response = await api.put<PatientMedicalInfoResponse>(
      `/v1/doctor/patients/${patientId}/medical`,
      payload
    )
    return response.data
  } catch (error) {
    console.error('Failed to update patient medical information:', error)
    throw error
  }
}

