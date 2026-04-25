import {
  deleteAward,
  getAllAwards,
  saveAward,
  updateAward
} from '../services/awards-service'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Award } from '@/types/award'

export const useAwards = () => {
  const queryClient = useQueryClient()

  // Fetch Award
  const {
    data: awards,
    isLoading,
    error
  } = useQuery<Award[], Error>({
    queryKey: ['awards'],
    queryFn: getAllAwards,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save award
  const saveMutation = useMutation({
    mutationFn: saveAward,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['awards'] })
    },
    onError: (error) => {
      console.error('Failed to save award:', error)
    }
  })

  // Update Award
  const updateMutation = useMutation({
    mutationFn: ({ awardId, data }: { awardId: string; data: Award }) =>
      updateAward(awardId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['awards'] })
    },
    onError: (error) => {
      console.error('Failed to update award:', error)
    }
  })

  // Delete award
  const deleteMutation = useMutation({
    mutationFn: deleteAward,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['awards'] })
    },
    onError: (error) => {
      console.error('Failed to delete award:', error)
    }
  })

  return {
    awards: awards || [],
    isLoading,
    error,
    saveAward: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updateAward: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteAward: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
