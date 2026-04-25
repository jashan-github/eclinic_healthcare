import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'
import type { TimeOffItem, TimeOffPayload } from '@/types/calendar'

export const fetchBlockedCalendarSlots = async (
  doctorId: string
): Promise<TimeOffItem[]> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<TimeOffItem[]>>(
      `/v1/doctors/${doctorId}/time-off`
    )

    return data.data
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const saveBlockCalendarSlot = async (
  doctorId: string,
  payload: TimeOffPayload
): Promise<void> => {
  try {
    await axiosInstance.post(`/v1/doctors/${doctorId}/time-off`, payload)
  } catch (error) {
    console.log(error)

    throw error
  }
}

export const deleteBlockCalendarSlot = async (
  timeOffId: string
): Promise<void> => {
  try {
    await axiosInstance.delete(`/v1/time-off/${timeOffId}`)
  } catch (error) {
    console.log(error)

    throw error
  }
}
