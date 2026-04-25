import { useQuery } from '@tanstack/react-query'
import {
  getPatientDocuments,
  type PatientDocumentsResponse,
  type GetPatientDocumentsParams
} from '@/services/doctor-patient-documents-service'

export const usePatientDocuments = (
  patientId: string | undefined,
  params?: GetPatientDocumentsParams
) => {
  return useQuery<PatientDocumentsResponse, Error>({
    queryKey: ['patientDocuments', patientId, params],
    queryFn: () => {
      if (!patientId) throw new Error('Patient ID is required')
      return getPatientDocuments(patientId, params)
    },
    enabled: !!patientId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

