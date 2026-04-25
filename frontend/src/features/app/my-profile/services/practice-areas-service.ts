import axiosInstance from '@/lib/api'
import type { PracticeAreaCompact } from '@/types/practice-area'

export const getAllPracticeAreas = async (): Promise<PracticeAreaCompact[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/practices')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const savePracticeArea = async (practices: PracticeAreaCompact[]) => {
  try {
    const { data } = await axiosInstance.post('/v5/doctor/profile/practices', {
      practices
    })

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deletePracticeArea = async (practiceAreaId: string) => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/practices/${practiceAreaId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
