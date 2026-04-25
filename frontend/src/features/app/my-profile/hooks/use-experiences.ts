import {
  deleteExperience,
  fetchAllExperiences,
  saveExperience,
  updateExperience
} from '@/features/app/my-profile/services/experiences-service'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Experience } from '@/types/experience'

export const useExperiences = () => {
  const queryClient = useQueryClient()

  // Fetch Experiences
  const {
    data: experiences,
    isLoading,
    error
  } = useQuery<Experience[], Error>({
    queryKey: ['experiences'],
    queryFn: fetchAllExperiences,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save Experience
  const saveMutation = useMutation({
    mutationFn: saveExperience,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
    },
    onError: (error) => {
      console.error('Failed to save experience:', error)
    }
  })

  // Update Experience
  const updateMutation = useMutation({
    mutationFn: ({
      experienceId,
      data
    }: {
      experienceId: string
      data: Experience
    }) => updateExperience(experienceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
    },
    onError: (error) => {
      console.error('Failed to update experience:', error)
    }
  })

  // Delete Experience
  const deleteMutation = useMutation({
    mutationFn: deleteExperience,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiences'] })
    },
    onError: (error) => {
      console.error('Failed to delete experience:', error)
    }
  })

  return {
    experiences: experiences || [],
    isLoading,
    error,
    saveExperience: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updateExperience: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteExperience: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
