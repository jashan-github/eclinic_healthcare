import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchDoctorPatients,
  fetchPatientDetails,
  fetchPatientMedicalInfo,
  updatePatientMedicalInfo,
  type DoctorPatientsResponse,
  type PatientDetailsResponse,
  type PatientMedicalResponse,
  type PatientMedicalInfo
} from '@/services/doctor-patients-service'
import { toast } from 'react-toastify'

/**
 * Hook to fetch doctor's patients list
 */
export const useDoctorPatients = () => {
  return useQuery<DoctorPatientsResponse, Error>({
    queryKey: ['doctorPatients'],
    queryFn: fetchDoctorPatients,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

/**
 * Hook to fetch patient details
 */
export const usePatientDetails = (patientId: string | undefined) => {
  return useQuery<PatientDetailsResponse, Error>({
    queryKey: ['patientDetails', patientId],
    queryFn: () => {
      if (!patientId) throw new Error('Patient ID is required')
      return fetchPatientDetails(patientId)
    },
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

/**
 * Hook to fetch patient medical information
 */
export const usePatientMedicalInfo = (patientId: string | undefined) => {
  return useQuery<PatientMedicalResponse, Error>({
    queryKey: ['patientMedicalInfo', patientId],
    queryFn: () => {
      if (!patientId) throw new Error('Patient ID is required')
      return fetchPatientMedicalInfo(patientId)
    },
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  })
}

/**
 * Hook to update patient medical information
 */
export const useUpdatePatientMedicalInfo = () => {
  const queryClient = useQueryClient()
  
  return useMutation<PatientMedicalResponse, Error, { patientId: string; data: Partial<PatientMedicalInfo> }>({
    mutationFn: ({ patientId, data }) => updatePatientMedicalInfo(patientId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['patientMedicalInfo', variables.patientId] })
      toast.success('Medical information updated successfully')
    },
    onError: (error: any) => {
      toast.error(error?.message || 'Failed to update medical information')
    },
  })
}

