// src/hooks/use-hipaa.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  submitHipaaReleaseForm,
  fetchHipaaReleaseForms,
  fetchHipaaReleaseFormById,
  type HipaaReleaseFormPayload,
  type HipaaReleaseFormResponse,
} from '../service/hipaa-service'
import { toast } from 'react-toastify'

// Hook to submit HIPAA release form
export const useSubmitHipaaForm = () => {
  const queryClient = useQueryClient()

  return useMutation<HipaaReleaseFormResponse, Error, HipaaReleaseFormPayload>({
    mutationFn: submitHipaaReleaseForm,
    onSuccess: () => {
      // Invalidate and refetch forms list
      queryClient.invalidateQueries({ queryKey: ['hipaa-release-forms'] })
      toast.success('HIPAA Form submitted successfully!')
    },
    onError: (error) => {
      console.error('Error submitting HIPAA form:', error)
      toast.error('Failed to submit HIPAA form. Please try again.')
    },
  })
}

// Hook to fetch all HIPAA release forms
export const useHipaaReleaseForms = () => {
  return useQuery<HipaaReleaseFormResponse[], Error>({
    queryKey: ['hipaa-release-forms'],
    queryFn: fetchHipaaReleaseForms,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

// Hook to fetch single HIPAA release form by ID
export const useHipaaReleaseFormById = (id: string) => {
  return useQuery<HipaaReleaseFormResponse, Error>({
    queryKey: ['hipaa-release-form', id],
    queryFn: () => fetchHipaaReleaseFormById(id),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
    enabled: !!id, // Only fetch if ID is provided
  })
}