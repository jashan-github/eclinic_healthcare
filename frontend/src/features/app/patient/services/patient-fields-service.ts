import axiosInstance from '@/lib/api'
import type { PatientConfigurationField } from '@/types/patient'

export const fetchPatientFields = async (): Promise<
  PatientConfigurationField[]
> => {
  try {
    const { data } = await axiosInstance.get(
      '/v5/doctor/patients/configurations?type=fields'
    )

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const savePatientFieldsService = async (
  data: PatientConfigurationField[]
) => {
  try {
    await axiosInstance.post('/v5/doctor/patients/configurations', {
      fields: data
    })
  } catch (error) {
    console.log(error)

    throw error
  }
}
