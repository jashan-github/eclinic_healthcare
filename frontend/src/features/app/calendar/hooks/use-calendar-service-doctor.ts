// src/hooks/use-calendar-service.ts
import type { AppointmentServiceDetail } from '@/types/calendar'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deleteCalendarService, getCalendarServices } from '../services/calendar-services-service-doctor'

export const useCalendarService = () => {
  const { data, isLoading, error } = useQuery<AppointmentServiceDetail[], Error>({
    queryKey: ['calendarServices'],
    queryFn: getCalendarServices,
    staleTime: 1000 * 60 * 5
  })

  // Services are already a flat array from the new endpoint
  const allServices: AppointmentServiceDetail[] = (data || []).filter(
    (service) => service && service.id
  )

  const calendarServicesFormatted = allServices.map(service => {
    const serviceName = service?.service_name || 'Unnamed Service'
    const nickname = service?.nickname
    const price = service?.amount || 0
    const serviceMode = service?.type || ''
    const appointmentType = (service as any)?.appointment_type || ''
    const paymentMethod = service?.payment_method || ''
    
    // Format service mode for display
    const formattedServiceMode = serviceMode === 'IN_CLINIC' 
      ? 'In-Clinic' 
      : serviceMode === 'TELECONSULTATION' 
        ? 'Teleconsultation' 
        : serviceMode
    
    // Format appointment type for display
    const formattedAppointmentType = appointmentType === 'REGULAR'
      ? 'Regular'
      : appointmentType === 'FOLLOW_UP'
        ? 'Follow-up'
        : appointmentType
    
    // Format payment type for display
    const formattedPaymentType = paymentMethod === 'prepaid' || paymentMethod === 'PREPAID'
      ? 'Prepaid'
      : paymentMethod === 'postpaid' || paymentMethod === 'POSTPAID'
        ? 'Postpaid'
        : paymentMethod
    
    // Build label with all information
    let label = nickname ? `${nickname} (${serviceName})` : serviceName
    label += ` - $${price}`
    if (formattedServiceMode) {
      label += ` - ${formattedServiceMode}`
    }
    if (formattedAppointmentType) {
      label += ` - ${formattedAppointmentType}`
    }
    if (formattedPaymentType) {
      label += ` - ${formattedPaymentType}`
    }
    
    return {
      value: service.id,
      label: label
    }
  })

  return {
    calendarServices: allServices,           // full objects → amount, duration, nickname
    calendarServicesFormatted,               // dropdown options
    isLoading,
    error
  }
}

export const useDeleteCalendarService = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteCalendarService,
    onSuccess: () => {
      // Invalidate and refetch the list
      queryClient.invalidateQueries({ queryKey: ['calendarServices'] })
    },
    onError: (error) => {
      console.error('Failed to delete service:', error)
      // toast.error('Failed to delete service')
    }
  })
}