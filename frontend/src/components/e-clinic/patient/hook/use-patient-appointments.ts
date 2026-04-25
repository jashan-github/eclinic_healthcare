// src/hooks/use-patient-appointments.ts
import { useQuery } from '@tanstack/react-query'
import { fetchGroupedAppointments, type GroupedAppointments } from '../service/patient-appointment-service'

export const usePatientAppointments = () => {
  return useQuery<GroupedAppointments, Error>({
    queryKey: ['patient-appointments-grouped'],
    queryFn: fetchGroupedAppointments,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}