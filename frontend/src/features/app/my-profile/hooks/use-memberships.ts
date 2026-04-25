import {
  deleteMembership,
  getAllMemberships,
  saveMembership,
  updateMembership
} from '@/features/app/my-profile/services/membership-service'
import type { Membership } from '@/types/membership'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const useMemberships = () => {
  const queryClient = useQueryClient()

  // Get all Memberships
  const {
    data: memberships,
    isLoading,
    error
  } = useQuery<Membership[], Error>({
    queryKey: ['basicDetailsMemberships'],
    queryFn: getAllMemberships,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  // Save membership
  const saveMutation = useMutation({
    mutationFn: saveMembership,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsMemberships'] })
    },
    onError: (error) => {
      console.error('Failed to save membership:', error)
    }
  })

  // Update Membership information
  const updateMutation = useMutation({
    mutationFn: ({
      membershipId,
      data
    }: {
      membershipId: string
      data: Membership
    }) => updateMembership(membershipId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsMemberships'] })
    },
    onError: (error) => {
      console.error('Failed to update membership:', error)
    }
  })

  // Delete membership
  const deleteMutation = useMutation({
    mutationFn: deleteMembership,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['basicDetailsMemberships'] })
    },
    onError: (error) => {
      console.error('Failed to delete membership:', error)
    }
  })

  return {
    memberships: memberships || [],
    isLoading,
    error,
    saveMembership: saveMutation.mutate,
    isSaving: saveMutation.isPending,
    updateMembership: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteMembership: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending
  }
}
