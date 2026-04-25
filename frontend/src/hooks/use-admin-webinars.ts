// src/hooks/use-admin-webinars.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchAdminWebinars,
  fetchAdminWebinarById,
  createAdminWebinar,
  updateAdminWebinar,
  deleteAdminWebinar,
  type AdminWebinarsResponse,
  type AdminWebinarDetailResponse,
  type UpdateWebinarPayload,
} from '@/services/admin-webinar-service'

// Fetch all webinars
export const useAdminWebinars = () => {
  return useQuery<AdminWebinarsResponse, Error>({
    queryKey: ['admin-webinars'],
    queryFn: fetchAdminWebinars,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    retry: 2,
  })
}

// Fetch a specific webinar by ID
export const useAdminWebinarById = (webinarId: string | null) => {
  return useQuery<AdminWebinarDetailResponse, Error>({
    queryKey: ['admin-webinar', webinarId],
    queryFn: () => {
      if (!webinarId) {
        throw new Error('Webinar ID is required')
      }
      return fetchAdminWebinarById(webinarId)
    },
    enabled: !!webinarId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })
}

// Create a new webinar
export const useCreateAdminWebinar = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createAdminWebinar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-webinars'] })
    },
  })
}

// Update a webinar
export const useUpdateAdminWebinar = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ webinarId, payload }: { webinarId: string; payload: UpdateWebinarPayload }) =>
      updateAdminWebinar(webinarId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-webinars'] })
      queryClient.invalidateQueries({ queryKey: ['admin-webinar'] })
    },
  })
}

// Delete a webinar
export const useDeleteAdminWebinar = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteAdminWebinar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-webinars'] })
    },
  })
}

