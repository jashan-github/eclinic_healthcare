import axiosInstance from '@/lib/api'
import type { MedicalUniversity } from '@/types/medical-university'

export const getAllMedicalUniversities = async (): Promise<
  MedicalUniversity[]
> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/medical-universities')

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}
