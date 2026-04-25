// src/hooks/use-rx-template.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchRxTemplate, saveRxTemplate, updateRxTemplate, type RxTemplateResponse, type SaveRxTemplatePayload } from '@/services/rx-template-service'
import { toast } from 'react-toastify'

export const useRxTemplate = (clinicLocationId?: string) => {
  return useQuery<RxTemplateResponse, Error>({
    queryKey: ['rx-template', clinicLocationId],
    queryFn: () => fetchRxTemplate(clinicLocationId),
    enabled: true, // Always enabled - fetch all or filter by location
    staleTime: 5 * 60 * 1000,
  })
}

export const useSaveRxTemplate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: SaveRxTemplatePayload & { templateId?: string }) => {
      if (payload.templateId) {
        return updateRxTemplate(payload.templateId, payload)
      } else {
        return saveRxTemplate(payload)
      }
    },
    onSuccess: () => {
      toast.success('Rx Template saved successfully!')
      queryClient.invalidateQueries({ queryKey: ['rx-template'] })
      queryClient.invalidateQueries({ queryKey: ['clinic-locations'] })
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to save template')
    },
  })
}