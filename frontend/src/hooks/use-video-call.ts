// src/hooks/use-video-call.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createVideoSession,
  joinVideoSession,
  confirmJoinSuccess,
  reportJoinFailure,
  getWaitingRoomStatus,
  getVideoSessionStatus,
  retryVideoSession,
  endVideoSession,
  leaveChannel,
  type CreateVideoSessionPayload,
  type BaseResponse,
  type VideoSession,
  type JoinResponse,
  type WaitingRoomResponse
} from '../services/video-call-service'
import { toast } from 'react-toastify'

// Create session
export const useCreateVideoSession = () => {
  const queryClient = useQueryClient()
  return useMutation<BaseResponse<VideoSession>, Error, CreateVideoSessionPayload>({
    mutationFn: createVideoSession,
    onSuccess: (res) => {
      if (res.success) {
        toast.success('Session created')
        queryClient.invalidateQueries({ queryKey: ['videoSessions'] })
      }
    },
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Create failed')
  })
}

// Join session
export const useJoinVideoSession = () => {
  return useMutation<BaseResponse<JoinResponse>, Error, string>({
    mutationFn: joinVideoSession,
    onSuccess: (res) => {
      if (res.success) {
        if (res.data.waiting_room) {
          toast.info('In waiting room')
        } else if (res.data.token) {
          toast.success('Joined - token received')
          // Here: Use token to join Agora (in component)
        }
      }
    },
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Join failed')
  })
}

// Confirm join success
export const useConfirmJoinSuccess = () => {
  return useMutation<BaseResponse<VideoSession>, Error, string>({
    mutationFn: confirmJoinSuccess,
    onSuccess: (res) => res.success && toast.success('Join confirmed'),
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Confirm failed')
  })
}

// Report join failure
export const useReportJoinFailure = () => {
  return useMutation<BaseResponse<VideoSession>, Error, string>({
    mutationFn: reportJoinFailure,
    onSuccess: (res) => res.success && toast.warn('Join failure reported'),
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Report failed')
  })
}

// Poll waiting room
export const useWaitingRoomStatus = (sessionId: string | null, enabled = false) => {
  return useQuery<BaseResponse<WaitingRoomResponse>, Error>({
    queryKey: ['waitingRoom', sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error('Session ID required')
      return getWaitingRoomStatus(sessionId)
    },
    enabled: !!sessionId && enabled,
    refetchInterval: (q) => {
      const data = q.state.data?.data
      if (data && data.both_ready && !data.waiting_room && data.token) {
        return false
      }
      return 3000
    },
    retry: false
  })
}

// Get status
export const useVideoSessionStatus = (sessionId: string | null, enabled = false) => {
  return useQuery<BaseResponse<VideoSession>, Error>({
    queryKey: ['videoSessionStatus', sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error('Session ID required')
      return getVideoSessionStatus(sessionId)
    },
    enabled: !!sessionId && enabled,
    refetchInterval: 10000,
    retry: false
  })
}

// Retry
export const useRetryVideoSession = () => {
  return useMutation<BaseResponse<VideoSession>, Error>({
    mutationFn: retryVideoSession,
    onSuccess: (res) => res.success && toast.success('Retry successful'),
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Retry failed')
  })
}

// End
export const useEndVideoSession = () => {
  return useMutation<BaseResponse<VideoSession>, Error, string>({
    mutationFn: endVideoSession,
    onSuccess: (res) => res.success && toast.success('Session ended'),
    onError: (err: any) => toast.error(err?.response?.data?.message || 'End failed')
  })
}

// Leave channel
export const useLeaveChannel = () => {
  return useMutation<BaseResponse<any>, Error, string>({
    mutationFn: leaveChannel,
  })
}