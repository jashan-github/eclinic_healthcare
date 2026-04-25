import api from '@/lib/api'

export interface VitalItem {
  name: string
  unit: string
  current: number | string | null
  [date: string]: number | string | null // dynamic date keys
}

export interface VitalsResponse {
  status: boolean
  data: {
    dates: string[]
    vitals: VitalItem[]
    current_date: string
  }
}

export const fetchPatientVitals = async (patientId: string, limit = 20): Promise<VitalsResponse['data']> => {
  try {
    const response = await api.get<VitalsResponse>(
      `/v1/patient-vital-signs/patient/${patientId}`,
      { params: { limit } }
    )
    console.log('📡 Patient vital signs response:', response.data)
    return response.data.data
  } catch (error: any) {
    console.error(`Failed to fetch vitals for patient ID: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to load vital signs')
  }
}

export const updatePatientVitals = async (
  patientId: string,
  updates: { field_name: string; value: number | string; unit: string }[]
) => {
  try {
    console.log('📡 Updating patient vital signs:', { patientId, vitals: updates })
    const response = await api.post(`/v1/patient-vital-signs/patient/${patientId}`, {
      vitals: updates
    })
    console.log('✅ Vitals updated successfully:', response.data)
    return response.data
  } catch (error: any) {
    console.error('Failed to update vitals', error)
    throw new Error(error.response?.data?.message || 'Failed to save vital signs')
  }
}