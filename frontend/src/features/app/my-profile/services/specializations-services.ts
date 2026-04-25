import type { Specialization } from '@/types/specialization'
import axiosInstance from '@/lib/api'

export const getAllSpecializations = async (): Promise<Specialization[]> => {
  try {
    const { data } = await axiosInstance.get(
      '/v1/medical-services/'
    )

    return {data}.data.data.medical_services
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const postSpecializations = async (
  data: Specialization[]
): Promise<void> => {
  try {
    await axiosInstance.post('/v5/doctor/profile/specializations', data)
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteSpecialization = async (
  specializationId: string
): Promise<void> => {
  try {
    await axiosInstance.delete(
      `/v5/doctor/profile/specializations/${specializationId}`
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}
