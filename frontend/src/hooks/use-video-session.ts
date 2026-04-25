import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createVideoSession,
  joinVideoSession,
  confirmJoinSuccess,
  reportJoinFailure,
  getWaitingRoomStatus,
  retryVideoSession,
  endVideoSession,
  type CreateVideoSessionPayload,
  type VideoSession,
  type JoinSessionResponse,
  type WaitingRoomStatus,
  type RetrySessionPayload
} from '@/services/video-session-service'
import { toast } from 'react-toastify'

/**
 * Hook to create a new video session
 */
export const useCreateVideoSession = () => {
  return useMutation<VideoSession, Error, CreateVideoSessionPayload>({
    mutationFn: createVideoSession,
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to create video session')
    }
  })
}

/**
 * Hook to join a video session
 */
export const useJoinVideoSession = () => {
  return useMutation<JoinSessionResponse, Error, { sessionId: string; userId?: string; role?: string }>({
    mutationFn: ({ sessionId, userId, role }) => joinVideoSession(sessionId, userId, role),
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to join video session')
    }
  })
}

/**
 * Hook to confirm join success (for billing)
 */
export const useConfirmJoinSuccess = () => {
  const queryClient = useQueryClient()
  
  return useMutation<void, Error, string>({
    mutationFn: confirmJoinSuccess,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videoSession'] })
    },
    onError: (error: any) => {
      console.error('Failed to confirm join success:', error)
      // Don't show toast as this is automatic
    }
  })
}

/**
 * Hook to report join failure
 */
export const useReportJoinFailure = () => {
  const queryClient = useQueryClient()
  
  return useMutation<void, Error, { sessionId: string; error: string; errorCode?: string }>({
    mutationFn: ({ sessionId, error, errorCode }) => reportJoinFailure(sessionId, error, errorCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videoSession'] })
      toast.error('Failed to join session. Please try again.')
    },
    onError: (error: any) => {
      console.error('Failed to report join failure:', error)
    }
  })
}

/**
 * Hook to get waiting room status (polling for patients)
 */
export const useWaitingRoomStatus = (sessionId: string | null, enabled: boolean = true) => {
  return useQuery<WaitingRoomStatus, Error>({
    queryKey: ['waitingRoom', sessionId],
    queryFn: () => {
      if (!sessionId) throw new Error('Session ID is required')
      return getWaitingRoomStatus(sessionId)
    },
    enabled: enabled && !!sessionId,
    refetchInterval: 3000, // Poll every 3 seconds
    retry: 3
  })
}

/**
 * Hook to retry a failed session
 */
export const useRetryVideoSession = () => {
  const queryClient = useQueryClient()
  
  return useMutation<VideoSession, Error, RetrySessionPayload>({
    mutationFn: retryVideoSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videoSession'] })
      toast.success('Session retry initiated')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to retry session')
    }
  })
}

/**
 * Hook to end a video session
 */
export const useEndVideoSession = () => {
  const queryClient = useQueryClient()
  
  return useMutation<void, Error, string>({
    mutationFn: endVideoSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videoSession'] })
      toast.success('Session ended successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to end session')
    }
  })
}

