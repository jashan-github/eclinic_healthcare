// src/services/calendar-services-service.ts
import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'
import type { AppointmentServiceDetail } from '@/types/calendar'

export const getCalendarServices = async (): Promise<AppointmentServiceDetail[]> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<AppointmentServiceDetail[]>>(
      '/v1/admin/services'
    )

    return data.data
  } catch (error) {
    console.log(error)
    throw error
  }
}

export const deleteCalendarService = async (serviceId: string): Promise<void> => {
  try {
    await axiosInstance.delete(
      `/v1/admin/services/${serviceId}`
    )
  } catch (error) {
    console.error('Delete service failed:', error)
    throw error
  }
}