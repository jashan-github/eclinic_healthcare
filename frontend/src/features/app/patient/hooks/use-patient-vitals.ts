// src/hooks/use-patient-vitals.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { fetchPatientVitals } from '../services/patient-vitals-service'

export const usePatientVitals = (patientId: string | undefined, limit = 20) => {
  const queryClient = useQueryClient()

  // Fetch vitals
  const query = useQuery({
    queryKey: ['patient-vitals', patientId, limit],
    queryFn: async () => {
      if (!patientId) throw new Error('Patient ID is required')
      return await fetchPatientVitals(patientId, limit)
    },
    enabled: !!patientId,
    staleTime: 10 * 60 * 1000,
    retry: 2,
  })

  // Update vitals (POST to backend)
  const mutation = useMutation({
    mutationFn: async (payload: Record<string, any>) => {
      if (!patientId) throw new Error('Patient ID is required')
      await api.post(`/v1/patient-vital-signs/patient/${patientId}`, payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-vitals', patientId, limit] })
    },
  })

  return {
    ...query,
    updateVitals: mutation.mutateAsync,
    isSaving: mutation.isPending,
    saveError: mutation.error,
  }
}