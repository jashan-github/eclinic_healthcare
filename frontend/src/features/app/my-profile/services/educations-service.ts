import type { Education } from '@/types/education'
import axiosInstance from '@/lib/api'

export const fetchAllEducations = async (): Promise<Education[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/educations')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveEducation = async (data: Education): Promise<Education[]> => {
  try {
    const { data: res } = await axiosInstance.post(
      '/v5/doctor/profile/educations',
      data
    )

    return res.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const updateEducation = async (
  educationId: string,
  data: Education
): Promise<void> => {
  try {
    await axiosInstance.put(
      `/v5/doctor/profile/educations/${educationId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteEducation = async (educationId: string): Promise<void> => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/educations/${educationId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
