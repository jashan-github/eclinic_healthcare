// src/hooks/use-doctor-patient-details.ts
import { useQuery } from '@tanstack/react-query'
import { fetchPatientDetails, type PatientDetailsResponse } from '@/services/doctor-patient-details'

export const useDoctorPatientDetails = (patientId: string) => {
  return useQuery<PatientDetailsResponse, Error>({
    queryKey: ['patient-details', patientId],
    queryFn: () => fetchPatientDetails(patientId),
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  })
}