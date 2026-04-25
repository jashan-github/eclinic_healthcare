// hooks/use-block-calendar-slots.ts

import type { TimeOffItem, TimeOffPayload } from '@/types/calendar'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import { useAuth } from '@/context/auth/auth-context-utils'
import {
  fetchBlockedCalendarSlots,
  saveBlockCalendarSlot,
  deleteBlockCalendarSlot
} from '../services/block-calendar-slots-service'

export const useBlockCalendarSlots = () => {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const doctorId = user?.id

  // Fetch blocked slots
  const { data, isLoading, error } = useQuery<TimeOffItem[], Error>({
    queryKey: ['blockedCalendarSlots', doctorId],
    queryFn: () => {
      if (!doctorId) {
        throw new Error('Healthcare Provider ID is required')
      }
      return fetchBlockedCalendarSlots(doctorId)
    },
    enabled: !!doctorId,
    staleTime: 1000 * 60 * 5,
  })

  // Save new blocked slots
  const saveMutation = useMutation({
    mutationFn: (payload: TimeOffPayload) => {
      if (!doctorId) {
        throw new Error('Healthcare Provider ID is required')
      }
      return saveBlockCalendarSlot(doctorId, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blockedCalendarSlots', doctorId] })
      toast.success('Calendar blocked successfully!')
    },
    onError: () => {
      toast.error('Failed to block calendar. Please try again.')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: deleteBlockCalendarSlot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blockedCalendarSlots', doctorId] })
      toast.success('Blocked slot removed!')
    },
    onError: () => {
      toast.error('Failed to delete blocked slot.')
    }
  })

  return {
    blockedSlots: data || [],
    isLoading,
    error,

    // Save
    saveBlockCalendarSlots: saveMutation.mutate,
    isSaving: saveMutation.isPending,

    // Delete function
    deleteBlockedSlot: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  }
}