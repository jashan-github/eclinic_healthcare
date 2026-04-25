// src/hooks/use-request-handle.ts

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { acceptRequest, getDoctorWaiverSettings, rejectRequest, type RejectRequestPayload } from '../services/request-handle-service'

export const useDoctorWaiverSettings = () => {
  return useQuery({
    queryKey: ['doctor-waiver-settings'],
    queryFn: getDoctorWaiverSettings,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}

export const useAcceptRequest = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ requestId, waiverPercent }: { requestId: string; waiverPercent?: number }) =>
      acceptRequest(requestId, waiverPercent !== undefined ? { waiver_percent: waiverPercent } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-pending-requests'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-processed-requests'] })
    },
  })
}

export const useRejectRequest = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: string; payload: RejectRequestPayload }) =>
      rejectRequest(requestId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-pending-requests'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-processed-requests'] })
    },
  })
}