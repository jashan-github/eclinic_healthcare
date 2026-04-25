import axiosInstance from '@/lib/api'
import type { ClinicPhoto, ClinicPhotoRaw } from '@/types/clinic'

export const getAllClinicPhotos = async (): Promise<ClinicPhoto[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/clinic/gallery/images')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveClinicPhoto = async (data: ClinicPhotoRaw): Promise<void> => {
  try {
    await axiosInstance.post('/v5/doctor/clinic/gallery/images', data, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteClinicPhoto = async (
  clinicPhotoId: string
): Promise<void> => {
  try {
    await axiosInstance.delete(
      `/v5/doctor/clinic/gallery/images/${clinicPhotoId}`
    )
  } catch (error) {
    console.log(error)

    throw error
  }
}
