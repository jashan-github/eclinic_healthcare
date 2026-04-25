import type { BasicDetails } from '@/types/doctor'
import axiosInstance from '@/lib/api'

export const getBasicDetails = async (): Promise<BasicDetails> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/about')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const postBasicDetails = async (data: BasicDetails) => {
  try {
    const response = await axiosInstance.post('/v5/doctor/profile/about', data)

    return response.data
  } catch (error) {
    console.log(error)

    throw error
  }
}
