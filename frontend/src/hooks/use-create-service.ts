// src/hooks/use-create-service.ts
import {
  createService,
  type CreateServicePayload,
  type CreatedServiceData
} from '@/services/create-service'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'

export const useCreateService = () => {
  const queryClient = useQueryClient()

  return useMutation<
    CreatedServiceData,
    Error,
    CreateServicePayload
  >({
    mutationFn: createService,

    onSuccess: (newService) => {
      toast.success(`Service "${newService.service_name}" created successfully!`)

      // Invalidating common service-related queries
      queryClient.invalidateQueries({ queryKey: ['calendar-services'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-services'] })
      queryClient.invalidateQueries({ queryKey: ['services'] })
    },

    onError: (error) => {
      toast.error(error.message || 'Failed to create service')
    }
  })
}