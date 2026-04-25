import axiosInstance from '@/lib/api'
import type { Registration } from '@/types/registration'

export const getAllRegistrations = async (): Promise<Registration[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/profile/registrations')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveRegistration = async (data: Registration): Promise<void> => {
  try {
    await axiosInstance.post('/v5/doctor/profile/registrations', data)
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const updateRegistration = async (
  registrationId: string,
  data: Registration
): Promise<void> => {
  try {
    await axiosInstance.put(
      `/v5/doctor/profile/registrations/${registrationId}`,
      data
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteRegistration = async (
  registrationId: string
): Promise<void> => {
  try {
    await axiosInstance.delete(
      `/v5/doctor/profile/registrations/${registrationId}`
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}
