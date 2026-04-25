import axiosInstance from '@/lib/api'
import type {
  PatientMedicalHistoryPayload,
  PatientMedicalHistoryResponse
} from '@/types/patient'

export const fetchPatientMedicalHistoryService =
  async (): Promise<PatientMedicalHistoryResponse> => {
    try {
      const { data } = await axiosInstance.get(
        '/v5/doctor/patients/configurations?type=medical_history'
      )

      return data.data
    } catch (error) {
      console.log(error)

      throw error
    }
  }

export const savePatientMedicalHistoryService = async (
  data: PatientMedicalHistoryPayload
) => {
  try {
    await axiosInstance.post('/v5/doctor/patients/configurations', data)
  } catch (error) {
    console.log(error)

    throw error
  }
}
