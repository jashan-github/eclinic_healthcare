import {
  deletePracticeArea,
  getAllPracticeAreas,
  savePracticeArea
} from '@/features/app/my-profile/services/practice-areas-service'
import type { PracticeAreaCompact } from '@/types/practice-area'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const usePracticeAreas = () => {
  const queryClient = useQueryClient()

  // Fetch PracticeAreas
  const {
    data: practiceAreas,
    isLoading,
    error
  } = useQuery<PracticeAreaCompact[], Error>({
    queryKey: ['basicDetailsPracticeAreas'],
    queryFn: getAllPracticeAreas,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save practiceArea
  const saveMutation = useMutation({
    mutationFn: savePracticeArea,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsPracticeAreas'] })
    },
    onError: (error) => {
      console.error('Failed to save practiceArea:', error)
    }
  })

  // Delete practiceArea
  const deleteMutation = useMutation({
    mutationFn: deletePracticeArea,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsPracticeAreas'] })
    },
    onError: (error) => {
      console.error('Failed to delete practiceArea:', error)
    }
  })

  return {
    practiceAreas: practiceAreas || [],
    isLoading,
    error,
    savePracticeArea: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    deletePracticeArea: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
