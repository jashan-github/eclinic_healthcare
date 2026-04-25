import {
  deleteRegistration,
  getAllRegistrations,
  saveRegistration,
  updateRegistration
} from '@/features/app/my-profile/services/registrations-service'
import type { Registration } from '@/types/registration'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const useRegistrations = () => {
  const queryClient = useQueryClient()

  // Fetch Registrations
  const {
    data: registrations,
    isLoading,
    error
  } = useQuery<Registration[], Error>({
    queryKey: ['basicDetailsRegistrations'],
    queryFn: getAllRegistrations,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save registration
  const saveMutation = useMutation({
    mutationFn: saveRegistration,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsRegistrations'] })
    },
    onError: (error) => {
      console.error('Failed to save registration:', error)
    }
  })

  // Update Registration information
  const updateMutation = useMutation({
    mutationFn: ({
      registrationId,
      data
    }: {
      registrationId: string
      data: Registration
    }) => updateRegistration(registrationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsRegistrations'] })
    },
    onError: (error) => {
      console.error('Failed to update registration:', error)
    }
  })

  // Delete registration
  const deleteMutation = useMutation({
    mutationFn: deleteRegistration,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsRegistrations'] })
    },
    onError: (error) => {
      console.error('Failed to delete registration:', error)
    }
  })

  return {
    registrations: registrations || [],
    isLoading,
    error,
    saveRegistration: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updateRegistration: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteRegistration: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
