// use-rx-service.ts
import { useQuery } from '@tanstack/react-query'
import { fetchRxPdf } from '../services/rx-service'

export const useRxPdf = (
  patientId: string,
  soapNoteId?: string,
  appointmentId?: string,
  rxTemplateId?: string
) => {
  const { data, isLoading, error } = useQuery<Blob, Error>({
    queryKey: ['rxPdf', patientId, soapNoteId, appointmentId, rxTemplateId],
    queryFn: () =>
      fetchRxPdf(patientId, soapNoteId!, appointmentId!, rxTemplateId!),
    enabled: !!soapNoteId && !!appointmentId && !!rxTemplateId,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    pdfBlob: data,
    isLoading,
    error
  }
}