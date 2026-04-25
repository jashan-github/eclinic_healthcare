import axiosInstance from '@/lib/api'
import type { MedicalCouncil } from '@/types/medical-council'

export const getAllMedicalCouncils = async (): Promise<MedicalCouncil[]> => {
  try {
    const { data } = await axiosInstance.get(
      '/v5/doctor/medical-registration-councils'
    )

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}
