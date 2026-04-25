import {
  deleteSpecialization,
  getAllSpecializations,
  postSpecializations
} from '@/features/app/my-profile/services/specializations-services'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Specialization } from '@/types/specialization'

export const useSpecializations = () => {
  const queryClient = useQueryClient()

  // Fetch specializations
  const { data, isLoading, error } = useQuery<Specialization[], Error>({
    queryKey: ['basicDetailsSpecializations'],
    queryFn: getAllSpecializations,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save/Update Specializations
  const mutation = useMutation({
    mutationFn: postSpecializations,
    onSuccess: () => {
      // Invalidate the basic details query to refetch updated data
      queryClient.invalidateQueries({
        queryKey: ['basicDetailsSpecializations']
      })
    },
    onError: (error) => {
      console.error('Failed to save settings:', error)
    }
  })

  // Delete specialization
  const deleteMutation = useMutation({
    mutationFn: deleteSpecialization,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['basicDetailsSpecializations']
      })
    },
    onError: (error) => {
      console.error('Failed to delete specialization:', error)
    }
  })

  return {
    specializations: data || [],
    isLoading,
    error,
    saveSpecialization: mutation.mutate,
    isSaving: mutation.isPending,
    deleteSpecialization: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
