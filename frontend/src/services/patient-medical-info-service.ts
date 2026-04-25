import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'

export interface PredefinedCondition {
  name: string
  years?: string
  selected: boolean
}

export interface CustomCondition {
  name: string
  years?: string
}

export interface ExistingCondition {
  name?: string
  years?: string
}

export interface Allergies {
  details?: string
  years?: string
}

export interface Medication {
  name: string
  dosage: string
  frequency: string
}

export interface PatientMedicalInfo {
  predefined_conditions?: PredefinedCondition[]
  custom_conditions?: CustomCondition[]
  existing_condition?: ExistingCondition
  allergies?: Allergies
  medications?: Medication[]
}

export interface UpdatePatientMedicalInfoPayload {
  predefined_conditions?: PredefinedCondition[]
  custom_conditions?: CustomCondition[]
  existing_condition?: ExistingCondition
  allergies?: Allergies
  medications?: Medication[]
}

// Mapping for predefined conditions (frontend label to backend key)
const predefinedMap: Record<string, string> = {
  'Diabetes mellitus': 'diabetes_mellitus',
  'Hypertension': 'hypertension',
  'Hypothyroidism': 'hypothyroidism',
  'Alcohol': 'alcohol',
  'Tobacco': 'tobacco',
  'Smoke': 'smoke'
}

export const getPatientMedicalInfo = async (): Promise<PatientMedicalInfo> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<any>>(
      '/v1/patients/profile/medical'
    )

    const apiMedicalInfo = data.data?.medical_info || {}

    // Parse predefined conditions
    const predefined_conditions: PredefinedCondition[] = Object.entries(predefinedMap).map(([label, key]) => {
      const years = apiMedicalInfo[`${key}_years`]
      return {
        name: label,
        selected: years !== null && years !== undefined,
        years: years?.toString() || ''
      }
    })

    return {
      predefined_conditions,
      custom_conditions: apiMedicalInfo.custom_conditions || [],
      existing_condition: {
        name: apiMedicalInfo.existing_condition || '',
        years: apiMedicalInfo.existing_condition_years?.toString() || ''
      },
      allergies: {
        details: apiMedicalInfo.allergies || '',
        years: apiMedicalInfo.allergies_years?.toString() || ''
      },
      medications: apiMedicalInfo.current_medications || []
    }
  } catch (error) {
    console.error('Error fetching patient medical info:', error)
    throw error
  }
}

export const updatePatientMedicalInfo = async (payload: UpdatePatientMedicalInfoPayload) => {
  try {
    const medical_info: any = {}

    // Transform predefined
    payload.predefined_conditions?.forEach(cond => {
      if (cond.selected) {
        const key = predefinedMap[cond.name]
        if (key) {
          medical_info[`${key}_years`] = cond.years ? parseInt(cond.years) : null
        }
      }
    })

    // Custom conditions
    if (payload.custom_conditions) {
      medical_info.custom_conditions = payload.custom_conditions.map(c => ({
        name: c.name,
        years: c.years ? parseInt(c.years) : null
      }))
    }

    // Existing condition
    if (payload.existing_condition?.name) {
      medical_info.existing_condition = payload.existing_condition.name
      medical_info.existing_condition_years = payload.existing_condition.years ? parseInt(payload.existing_condition.years) : null
    }

    // Allergies
    if (payload.allergies?.details) {
      medical_info.allergies = payload.allergies.details
      medical_info.allergies_years = payload.allergies.years ? parseInt(payload.allergies.years) : null
    }

    // Medications
    if (payload.medications) {
      medical_info.current_medications = payload.medications.filter(m => m.name)  // Filter empty
    }

    const response = await axiosInstance.put<ApiResponse<PatientMedicalInfo>>(
      '/v1/patients/profile/medical',
      { medical_info }
    )

    return response.data.data
  } catch (error) {
    console.error('Error updating patient medical info:', error)
    throw error
  }
}