import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'
import type { TimeOffItem, TimeOffPayload } from '@/types/calendar'

export const fetchBlockedCalendarSlots = async (
  doctorId: string
): Promise<TimeOffItem[]> => {
  const { data } = await axiosInstance.get<ApiResponse<TimeOffItem[]>>(
    `/v1/doctors/${doctorId}/time-off`
  )

  return data.data
}

export const saveBlockCalendarSlot = async (
  doctorId: string,
  payload: TimeOffPayload
): Promise<void> => {
  await axiosInstance.post(`/v1/doctors/${doctorId}/time-off`, payload)
}

export const deleteBlockCalendarSlot = async (
  timeOffId: string
): Promise<void> => {
  await axiosInstance.delete(`/v1/time-off/${timeOffId}`)
}
