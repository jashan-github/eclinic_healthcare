// src/hooks/use-patient-visits.ts
import { useQuery } from '@tanstack/react-query'
import { fetchPatientVisits, fetchRxTemplates, type PatientVisitsResponse, type RxTemplatesResponse } from '../services/patient-visits-service'

export const usePatientVisits = (patientId: string | undefined) => {
  return useQuery<PatientVisitsResponse, Error>({
    queryKey: ['patient-visits', patientId],
    queryFn: () => {
      if (!patientId) throw new Error('Patient ID is required')
      return fetchPatientVisits(patientId)
    },
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000,
    retry: 2,
  })
}

export const useRxTemplates = () => {
  return useQuery<RxTemplatesResponse, Error>({
    queryKey: ['rx-templates'],
    queryFn: fetchRxTemplates,
    staleTime: 5 * 60 * 1000,
  })
}