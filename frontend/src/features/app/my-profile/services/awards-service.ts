import type { Award, AwardRaw } from '@/types/award'
import axiosInstance from '@/lib/api'
import type { ApiResponse } from '@/lib/api'

export const getAllAwards = async (): Promise<Award[]> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<Award[]>>(
      '/v5/doctor/profile/awards'
    )

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveAward = async (data: Award | AwardRaw) => {
  try {
    const response = await axiosInstance.post<ApiResponse<Award>>(
      '/v5/doctor/profile/awards',
      data
    )

    return response.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const updateAward = async (awardId: string, data: Award | AwardRaw) => {
  try {
    await axiosInstance.put<ApiResponse<Award>>(
      `/v5/doctor/profile/awards/${awardId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteAward = async (awardId: string): Promise<void> => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/awards/${awardId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
