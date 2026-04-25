import axiosInstance from '@/lib/api'
import type { SocialLinks } from '@/types/social-links'

export const fetchAllSocialLinks = async (): Promise<SocialLinks> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/social-links')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveAllSocialLinks = async (data: SocialLinks): Promise<void> => {
  try {
    await axiosInstance.post('/v5/doctor/profile/social-links', data)
  } catch (error) {
    console.log(error)

    throw error
  }
}
