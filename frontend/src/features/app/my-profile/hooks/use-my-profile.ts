import { useMutation, useQueryClient, useSuspenseQuery } from '@tanstack/react-query'
import { getMyProfileDetails } from '../services/my-profile-service'
import type { Profile } from '@/types/my-profile'
import { updateProfile } from '../services/edit-profile-service'

export const useMyProfile = () => {
  const queryClient = useQueryClient()

  const {
    data: myProfile,
    isLoading,
    error
  } = useSuspenseQuery<Profile, Error>({
    queryKey: ['myProfileDetails'],
    queryFn: getMyProfileDetails,
    staleTime: 1000 * 60 * 5
  })

  const updateMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myProfileDetails'] })
    }
  })

  return {
    myProfile: myProfile || null,
    isLoading,
    error,
    updateProfile: updateMutation.mutate,
    updateProfileAsync: updateMutation.mutateAsync,
    isUpdatingProfile: updateMutation.isPending,
  }
}