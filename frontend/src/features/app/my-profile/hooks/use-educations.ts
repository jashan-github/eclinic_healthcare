import {
  deleteEducation,
  fetchAllEducations,
  saveEducation,
  updateEducation
} from '@/features/app/my-profile/services/educations-service'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Education } from '@/types/education'

export const useEducations = () => {
  const queryClient = useQueryClient()

  // Fetch Education
  const {
    data: educations,
    isLoading,
    error
  } = useQuery<Education[], Error>({
    queryKey: ['educations'],
    queryFn: fetchAllEducations,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save education
  const saveMutation = useMutation({
    mutationFn: saveEducation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['educations'] })
    },
    onError: (error) => {
      console.error('Failed to save education:', error)
    }
  })

  // Update Education
  const updateMutation = useMutation({
    mutationFn: ({
      educationId,
      data
    }: {
      educationId: string
      data: Education
    }) => updateEducation(educationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['educations'] })
    },
    onError: (error) => {
      console.error('Failed to update education:', error)
    }
  })

  // Delete education
  const deleteMutation = useMutation({
    mutationFn: deleteEducation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['educations'] })
    },
    onError: (error) => {
      console.error('Failed to delete education:', error)
    }
  })

  return {
    educations: educations || [],
    isLoading,
    error,
    saveEducation: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updateEducation: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteEducation: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
