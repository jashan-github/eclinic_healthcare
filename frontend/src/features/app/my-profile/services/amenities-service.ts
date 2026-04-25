import axiosInstance from '@/lib/api'
import type { AmenityCategory } from '@/types/clinic'

export const getAmenities = async () => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/clinic/amenities')

    return data.data as AmenityCategory[]
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveAmenities = async (clinic_amenities: AmenityCategory[]) => {
  try {
    await axiosInstance.post('/v5/doctor/clinic/amenities', {
      clinic_amenities
    })
  } catch (error) {
    console.log(error)

    throw error
  }
}
