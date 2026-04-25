import type { Experience } from '@/types/experience'
import axiosInstance from '@/lib/api'

export const fetchAllExperiences = async (): Promise<Experience[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/experiences')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveExperience = async (data: Experience): Promise<Experience> => {
  try {
    const { data: response } = await axiosInstance.post(
      '/v5/doctor/profile/experiences',
      data
    )

    return response.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const updateExperience = async (
  experienceId: string,
  data: Experience
): Promise<void> => {
  try {
    await axiosInstance.put(
      `/v5/doctor/profile/experiences/${experienceId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteExperience = async (experienceId: string): Promise<void> => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/experiences/${experienceId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
