// src/hooks/use-create-new-service.ts
import {
  createNewService,
  type CreateNewServicePayload,
  type CreatedServiceData
} from '@/services/create-new-service'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'

export const useCreateNewService = () => {
  const queryClient = useQueryClient()

  return useMutation<
    CreatedServiceData,
    Error,
    CreateNewServicePayload
  >({
    mutationFn: createNewService,
    onSuccess: (data) => {
      toast.success(`Service "${data.service_name}" created successfully!`)
      queryClient.invalidateQueries({ queryKey: ['calendarServices'] })
    },
    onError: (error) => {
      toast.error(error.message || 'Unable to create service')
    }
  })
}