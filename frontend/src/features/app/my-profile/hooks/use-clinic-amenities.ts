import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getAmenities, saveAmenities } from '../services/amenities-service'
import type { AmenityCategory } from '@/types/clinic'

export const useClinicAmenities = () => {
  const queryClient = useQueryClient()

  // Get all amenities configuration
  const {
    data: amenities,
    isLoading,
    error
  } = useQuery<AmenityCategory[]>({
    queryKey: ['clinicAmenities'],
    queryFn: getAmenities,
    staleTime: 1000 * 60 * 5 // 5 Minutes
  })

  // Save amenities configuration
  const saveMutation = useMutation({
    mutationFn: saveAmenities,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clinicAmenities'] })
    },
    onError: (error) => {
      console.error('Failed to save award:', error)
    }
  })

  return {
    amenities,
    isLoading,
    error,
    saveAmenities: saveMutation.mutate,
    isSaving: saveMutation.isPending
  }
}
