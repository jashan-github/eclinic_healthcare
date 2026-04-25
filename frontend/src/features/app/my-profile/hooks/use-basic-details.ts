import {
  getBasicDetails,
  postBasicDetails
} from '@/features/app/my-profile/services/basic-details-service'
import type { BasicDetails } from '@/types/doctor'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const useBasicDetails = () => {
  const queryClient = useQueryClient()

  // Fetch Basic details for about you section
  const {
    data: basicDetails,
    isLoading,
    error
  } = useQuery<BasicDetails, Error>({
    queryKey: ['myProfileBasicDetails'],
    queryFn: getBasicDetails,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save basic details for about you section
  const mutation = useMutation({
    mutationFn: postBasicDetails,
    onSuccess: () => {
      // Invalidate the basic details query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['myProfileBasicDetails'] })
    },
    onError: (error) => {
      console.error('Failed to save!', error)
    }
  })

  return {
    basicDetails,
    isLoading,
    error,
    saveBasicDetails: mutation.mutate,
    isSaving: mutation.isPending
  }
}
