import axiosInstance from '@/lib/api'
import type { MedicalPracticeArea } from '@/types/medical-practice-area'

export const getMedicalPracticeAreas = async (
  params: { q?: string } = {}
): Promise<MedicalPracticeArea[]> => {
  try {
    const { data } = await axiosInstance.get(
      '/v5/doctor/get-medical-practices',
      { params }
    )

    return data.data
  } catch (error) {
    console.log(error)
    throw error
  }
}
