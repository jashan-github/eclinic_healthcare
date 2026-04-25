// src/services/calendar-services-service.ts
import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'
import type { AppointmentServiceDetail } from '@/types/calendar'

// API Response interface for the available services endpoint
interface AvailableServiceResponse {
  id: string
  name: string
  nickname: string | null
  service_mode: string
  appointment_type: string
  advance_booking_days: number
  minimum_notice_minutes: number
  payment_type: string
  price: number
}

export const getCalendarServices = async (): Promise<AppointmentServiceDetail[]> => {
  try {
    // Use GET /v1/doctor/services/available for the dropdown
    const { data } = await axiosInstance.get<ApiResponse<AvailableServiceResponse[]>>(
      '/v1/doctor/services/available'
    )

    // Handle both array response and nested data structure
    let services: AvailableServiceResponse[] = []
    
    if (Array.isArray(data.data)) {
      services = data.data
    } else if (Array.isArray(data)) {
      services = data
    }
    
    // Map API response to AppointmentServiceDetail format
    return services
      .filter((service) => {
        return service && service.id && service.name
      })
      .map((service): AppointmentServiceDetail & { appointment_type?: string } => ({
        id: service.id,
        service_name: service.name, // Map 'name' to 'service_name'
        nickname: service.nickname,
        doctor_id: '', // Not provided in API response
        appointment_treatment_id: '', // Not provided in API response
        amount: service.price, // Map 'price' to 'amount'
        duration: 30, // Default duration (not provided in API response)
        payment_method: service.payment_type?.toLowerCase() || null, // Map payment_type
        type: service.service_mode || '',
        appointment_type: service.appointment_type || '', // Store appointment_type for dropdown
        hasAdvanceBooking: service.advance_booking_days > 0 ? 1 : 0,
        allow_patient_booking: 1, // Default value
        advanceBookingFrom: service.advance_booking_days || 0,
        minimum_notice: service.minimum_notice_minutes || null,
        follow_up_validity: null, // Not provided in API response
        created_at: '', // Not provided in API response
        updated_at: '' // Not provided in API response
      }))
  } catch (error) {
    console.error('Error in getCalendarServices:', error)
    throw error
  }
}

export const deleteCalendarService = async (serviceId: string): Promise<void> => {
  try {
    await axiosInstance.delete(
      `/v1/doctor/availability-services/${serviceId}`
    )
  } catch (error) {
    console.error('Delete service failed:', error)
    throw error
  }
}