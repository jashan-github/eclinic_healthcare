// src/hooks/use-location.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchLocations,
  createLocation,
  updateLocation,
  deleteLocation,
  type LocationsResponse,

} from '../service/location-service'

export const useLocations = () => {
  const queryClient = useQueryClient()

  // Existing GET query – untouched
  const locationsQuery = useQuery<LocationsResponse, Error>({
    queryKey: ['locations'],
    queryFn: fetchLocations,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })

  // NEW: Create mutation
  const createMutation = useMutation({
    mutationFn: createLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
    },
  })

  // NEW: Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updateLocation>[1] }) =>
      updateLocation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
    },
  })

  // NEW: Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
    },
  })

  return {
    // GET
    data: locationsQuery.data,
    isLoading: locationsQuery.isLoading,
    error: locationsQuery.error,

    // CREATE
    createLocation: createMutation.mutate,
    isCreating: createMutation.isPending,

    // UPDATE
    updateLocation: updateMutation.mutate,
    isUpdating: updateMutation.isPending,

    // DELETE
    deleteLocation: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  }
}
