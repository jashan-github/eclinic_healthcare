// src/hooks/use-patient-details.ts

import { useQuery } from '@tanstack/react-query'
import { fetchPatientDetails, type PatientDetails } from '../services/patient-details-service'


export const useSinglePatientDetails = (patientId: string | undefined) => {
  return useQuery<PatientDetails, Error>({
    queryKey: ['patient-details', patientId],
    queryFn: () => {
      if (!patientId) throw new Error('Patient ID is required')
      return fetchPatientDetails(patientId)
    },
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
  })
}