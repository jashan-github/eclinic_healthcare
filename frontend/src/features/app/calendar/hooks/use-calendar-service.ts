// src/hooks/use-calendar-service.ts
import type { AppointmentServiceDetail } from '@/types/calendar'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deleteCalendarService, getCalendarServices } from '../services/calendar-services-service'

export const useCalendarService = () => {
  const { data, isLoading, error } = useQuery<AppointmentServiceDetail[], Error>({
    queryKey: ['calendarServices'],
    queryFn: getCalendarServices,
    staleTime: 1000 * 60 * 5
  })

  // No flattening needed - backend returns flat array
  const allServices: AppointmentServiceDetail[] = data ?? []

  const calendarServicesFormatted = allServices.map(service => ({
    value: service.id,
    label: service.nickname 
      ? `${service.nickname} (${service.service_name})` 
      : service.service_name
  }))

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