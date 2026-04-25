import type { Publication, PublicationRaw } from '@/types/publication'

import axiosInstance from '@/lib/api'

export const getAllPublications = async (): Promise<Publication[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/publications')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const savePublication = async (
  data: Publication | PublicationRaw
): Promise<void> => {
  try {
    await axiosInstance.post('/v5/doctor/profile/publications', data)
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const updatePublication = async (
  publicationId: string,
  data: Publication | PublicationRaw
): Promise<void> => {
  try {
    await axiosInstance.put(
      `/v5/doctor/profile/publications/${publicationId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deletePublication = async (awardId: string): Promise<void> => {
  try {
    await axiosInstance.delete(`/v5/doctor/profile/publications/${awardId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
