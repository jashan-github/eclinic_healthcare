import axiosInstance from '@/lib/api'
import type { MedicalDegree } from '@/types/medical-degree'

export const getAllMedicalDegrees = async (): Promise<MedicalDegree[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/medical-degrees')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}
