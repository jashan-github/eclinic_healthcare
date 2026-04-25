import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchPatientMedicalHistoryService,
  savePatientMedicalHistoryService
} from '../services/patient-medical-history-service'
import type { PatientMedicalHistoryResponse } from '@/types/patient'

export const usePatientMedicalHistory = () => {
  const queryClient = useQueryClient()

  // Get patient fields
  const { data, isLoading, error } = useQuery<
    PatientMedicalHistoryResponse,
    Error
  >({
    queryKey: ['patientMedicalHistory'],
    queryFn: fetchPatientMedicalHistoryService,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  const saveMutation = useMutation({
    mutationFn: savePatientMedicalHistoryService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patientMedicalHistory'] })
    },
    onError: (error) => {
      console.error('Failed to update patient fields:', error)
    }
  })

  return {
    patientMedicalHistory: data?.categories || [],
    isMedicalHistory: data ? data.is_medical_history : true,
    isLoading,
    error,
    savePatientMedicalHistory: saveMutation.mutate,
    isSaving: saveMutation.isPending
  }
}
