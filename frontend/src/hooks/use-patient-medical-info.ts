import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getPatientMedicalInfo, updatePatientMedicalInfo, type UpdatePatientMedicalInfoPayload } from '@/services/patient-medical-info-service'

export const usePatientMedicalInfo = () => {
  const queryClient = useQueryClient()

  const {
    data: medicalInfo,
    isLoading,
    error
  } = useQuery({
    queryKey: ['patientMedicalInfo'],
    queryFn: getPatientMedicalInfo,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  })

  const updateMutation = useMutation({
    mutationFn: updatePatientMedicalInfo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patientMedicalInfo'] })
    }
  })

  return {
    medicalInfo: medicalInfo || null,
    isLoading,
    error,
    updateMedicalInfo: (
      payload: UpdatePatientMedicalInfoPayload,
      options?: { onSuccess?: () => void; onError?: (error: any) => void }
    ) => {
      updateMutation.mutate(payload, {
        onSuccess: () => {
          options?.onSuccess?.()
        },
        onError: (error) => {
          options?.onError?.(error)
        }
      })
    },
    updateMedicalInfoAsync: updateMutation.mutateAsync,
    isUpdatingMedicalInfo: updateMutation.isPending,
  }
}

