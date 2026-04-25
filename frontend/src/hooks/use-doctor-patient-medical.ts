import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-toastify'
import {
  getPatientMedicalInfo,
  updatePatientMedicalInfo,
  type PatientMedicalInfoResponse,
  type UpdatePatientMedicalPayload
} from '@/services/doctor-patient-medical-service'

// Hook to fetch patient medical information
export const usePatientMedicalInfo = (patientId: string | null) => {
  return useQuery<PatientMedicalInfoResponse, Error>({
    queryKey: ['patient-medical-info', patientId],
    queryFn: () => {
      if (!patientId) {
        throw new Error('Patient ID is required')
      }
      return getPatientMedicalInfo(patientId)
    },
    enabled: !!patientId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1
  })
}

// Hook to update patient medical information
export const useUpdatePatientMedicalInfo = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      patientId,
      payload
    }: {
      patientId: string
      payload: UpdatePatientMedicalPayload
    }) => updatePatientMedicalInfo(patientId, payload),
    onSuccess: (_data, variables) => {
      toast.success('Medical information updated successfully!')
      // Invalidate and refetch the patient medical info
      queryClient.invalidateQueries({
        queryKey: ['patient-medical-info', variables.patientId]
      })
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.message ||
          error?.message ||
          'Failed to update medical information'
      )
    }
  })
}

