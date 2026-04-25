// src/hooks/use-appointment.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchDoctorAppointments,
  cancelAppointment,
  startTeleconsultation,
  type AppointmentResponse,
  type DoctorAppointmentsParams,
} from '@/services/appointment-service'

export const useDoctorAppointments = (params?: DoctorAppointmentsParams) => {
  return useQuery<AppointmentResponse['data'], Error>({
    queryKey: ['doctor-appointments', params],
    queryFn: () => fetchDoctorAppointments(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    retry: 2,
  })
}

// Mutation for cancelling appointment
export const useCancelAppointment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (appointmentId: string) => cancelAppointment(appointmentId),
    onSuccess: () => {
      // Invalidate and refetch appointments after cancel
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] })
    },
    onError: (error: any) => {
      console.error('Cancel appointment failed:', error)
    },
  })
}

// Mutation for starting call
export const useStartTeleconsultation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (appointmentId: string) => startTeleconsultation(appointmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-appointments'] })
    },
  })
}