import {
  deletePublication,
  getAllPublications,
  savePublication,
  updatePublication
} from '../services/publications-service'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { Publication } from '@/types/publication'

export const usePublications = () => {
  const queryClient = useQueryClient()

  // Fetch Publication
  const {
    data: publications,
    isLoading,
    error
  } = useQuery<Publication[], Error>({
    queryKey: ['publications'],
    queryFn: getAllPublications,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save publication
  const saveMutation = useMutation({
    mutationFn: savePublication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
    },
    onError: (error) => {
      console.error('Failed to save publication:', error)
    }
  })

  // Update Publication
  const updateMutation = useMutation({
    mutationFn: ({
      publicationId,
      data
    }: {
      publicationId: string
      data: Publication
    }) => updatePublication(publicationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
    },
    onError: (error) => {
      console.error('Failed to update publication:', error)
    }
  })

  // Delete publication
  const deleteMutation = useMutation({
    mutationFn: deletePublication,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications'] })
    },
    onError: (error) => {
      console.error('Failed to delete publication:', error)
    }
  })

  return {
    publications: publications || [],
    isLoading,
    error,
    savePublication: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updatePublication: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deletePublication: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
