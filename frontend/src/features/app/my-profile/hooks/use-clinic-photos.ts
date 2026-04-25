import type { ClinicPhoto } from '@/types/clinic'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import {
  deleteClinicPhoto,
  getAllClinicPhotos,
  saveClinicPhoto
} from '../services/clinic-photos-service'

export const useClinicPhotos = () => {
  const queryClient = useQueryClient()

  // Fetch Photos
  const {
    data: clinicPhotos,
    isLoading,
    error
  } = useQuery<ClinicPhoto[], Error>({
    queryKey: ['clinicPhotos'],
    queryFn: getAllClinicPhotos,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save photo
  const saveMutation = useMutation({
    mutationFn: saveClinicPhoto,
    onSuccess: () => {
      toast.success('Photo saved successfully!')
      queryClient.invalidateQueries({ queryKey: ['clinicPhotos'] })
    },
    onError: (error) => {
      console.error('Failed to save photo:', error)
      toast.error('Failed to save photo.')
    }
  })

  // Delete photo
  const deleteMutation = useMutation({
    mutationFn: deleteClinicPhoto,
    onSuccess: () => {
      toast.success('Photo deleted successfully!')
      queryClient.invalidateQueries({ queryKey: ['clinicPhotos'] })
    },
    onError: (error) => {
      console.error('Failed to delete photo:', error)
      toast.error('Failed to delete photo.')
    }
  })

  return {
    clinicPhotos: clinicPhotos || [],
    isLoading,
    error,
    saveClinicPhoto: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    deleteClinicPhoto: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
