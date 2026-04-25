import type { PatientConfigurationField } from '@/types/patient'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import {
  fetchPatientFields,
  savePatientFieldsService
} from '../services/patient-fields-service'

export const usePatientFields = () => {
  const queryClient = useQueryClient()

  // Get patient fields
  const { data, isLoading, error } = useQuery<
    PatientConfigurationField[],
    Error
  >({
    queryKey: ['patientFields'],
    queryFn: fetchPatientFields,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  const saveMutation = useMutation({
    mutationFn: savePatientFieldsService,
    onSuccess: () => {
      toast.success('Save successful!')
      queryClient.invalidateQueries({ queryKey: ['patientFields'] })
    },
    onError: (error) => {
      toast.error('Failed to update patient fields')
      console.error('Failed to update patient fields:', error)
    }
  })

  return {
    patientFields: data ?? [],
    selectedPatientFields: data ? data.filter((field) => field.selected) : [],
    isLoading,
    error,
    savePatientFields: saveMutation.mutate,
    isSaving: saveMutation.isPending
  }
}
