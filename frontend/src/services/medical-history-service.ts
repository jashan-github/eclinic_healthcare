import axiosInstance from '@/lib/api'

export const fetchMedicalHistoryOptions = async (type: string, q: string) => {
  try {
    const { data } = await axiosInstance(
      `/v5/doctor/patients/configurations/search?q=${q}&type=${type}`
    )

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}
