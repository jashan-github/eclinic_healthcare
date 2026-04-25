// src/hooks/use-appointment-request.ts
import { useMutation } from '@tanstack/react-query'
import { requestAppointment, type AppointmentRequestPayload, type AppointmentRequestResponse } from '../service/doctor-appointment-booking-service'

export const useAppointmentRequest = () => {
  return useMutation<AppointmentRequestResponse, Error, AppointmentRequestPayload>({
    mutationFn: requestAppointment,
    onSuccess: (data) => {
      console.log('Appointment request successful:', data)
      // You can add toast or other side effects here
    },
    onError: (error) => {
      console.error('Appointment request failed:', error)
      // Handle error globally if needed
    }
  })
}