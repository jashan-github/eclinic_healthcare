import axiosInstance from '@/lib/api'
import type { ScheduleDay } from '@/types/calendar'
import { 
  transformAvailabilityToScheduleDay,
  type DoctorAvailabilityResponse 
} from '@/services/weekly-schedule'

export const getSchedule = async (doctorId: string): Promise<ScheduleDay[]> => {
  try {
    if (!doctorId) {
      console.warn('Doctor ID not found, returning empty schedule')
      return []
    }

    // Fetch from new endpoint
    const response = await axiosInstance.get<DoctorAvailabilityResponse>(
      `/v1/doctors/${doctorId}/availability`
    )

    // Transform the response to ScheduleDay format (now async to fetch services)
    if (response.data?.success && Array.isArray(response.data.data)) {
      return await transformAvailabilityToScheduleDay(response.data.data)
    }

    return []
  } catch (error) {
    console.log(error)
    throw error
  }
}


export const deleteScheduleSlot = async (availabilityId: string): Promise<void> => {
  try {
    const response = await axiosInstance.delete(`/v1/availability/${availabilityId}`)
    return response.data
  } catch (error: any) {
    console.error('Failed to delete availability', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to delete availability'
    throw new Error(message)
  }
}
