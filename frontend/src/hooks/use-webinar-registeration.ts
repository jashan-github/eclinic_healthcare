// src/hooks/use-webinar-registeration.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { registerForWebinar } from '@/services/webinar-registeration'

export const useRegisterForWebinar = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: registerForWebinar,
    onSuccess: (data) => {
      // Only invalidate for free webinars (no payment_url means registration is complete)
      if (!data?.data?.payment?.payment_url) {
        toast.success(data.message || 'Registered for webinar successfully!')
        queryClient.invalidateQueries({ queryKey: ['patientWebinars'] })
        queryClient.invalidateQueries({ queryKey: ['doctor-webinars'] })
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to register for webinar')
    }
  })
}