import { useQuery, useMutation } from '@tanstack/react-query'
import {
  fetchStaffAssignedDoctorAppointments,
  fetchPatientContactDetails,
  fetchStaffStats,
  fetchStaffPatients,
  fetchStaffInvoices,
  downloadStaffInvoice,
  type StaffAppointmentsParams,
  type StaffAppointmentsResponse,
  type PatientContactDetailsResponse,
  type StaffStatsResponse,
  type StaffPatientsParams,
  type StaffPatientsResponse,
  type StaffInvoicesParams,
  type StaffInvoicesResponse,
} from '@/services/staff.service'

/**
 * Hook to fetch appointments for the assigned doctor
 */
export const useStaffAssignedDoctorAppointments = (params?: StaffAppointmentsParams) => {
  return useQuery<StaffAppointmentsResponse, Error>({
    queryKey: ['staff-assigned-doctor-appointments', params],
    queryFn: () => fetchStaffAssignedDoctorAppointments(params),
    staleTime: 1000 * 30, // 30 seconds
    refetchOnWindowFocus: true,
    retry: 1,
  })
}

/**
 * Hook to fetch patient contact details
 */
export const usePatientContactDetails = (patientId: string | null, enabled: boolean = true) => {
  return useQuery<PatientContactDetailsResponse, Error>({
    queryKey: ['staff-patient-contact-details', patientId],
    queryFn: () => {
      if (!patientId) {
        throw new Error('Patient ID is required')
      }
      return fetchPatientContactDetails(patientId)
    },
    enabled: enabled && !!patientId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 1,
  })
}

/**
 * Hook to fetch staff dashboard statistics
 */
export const useStaffStats = () => {
  return useQuery<StaffStatsResponse, Error>({
    queryKey: ['staff-stats'],
    queryFn: fetchStaffStats,
    staleTime: 1000 * 60, // 1 minute
    refetchOnWindowFocus: true,
    retry: 1,
  })
}

/**
 * Hook to fetch staff patients list
 */
export const useStaffPatients = (params?: StaffPatientsParams) => {
  return useQuery<StaffPatientsResponse, Error>({
    queryKey: ['staff-patients', params],
    queryFn: () => fetchStaffPatients(params),
    staleTime: 1000 * 30, // 30 seconds
    refetchOnWindowFocus: true,
    retry: 1,
  })
}

/**
 * Hook to fetch staff invoices list
 */
export const useStaffInvoices = (params?: StaffInvoicesParams) => {
  return useQuery<StaffInvoicesResponse, Error>({
    queryKey: ['staff-invoices', params],
    queryFn: () => fetchStaffInvoices(params),
    staleTime: 1000 * 30, // 30 seconds
    refetchOnWindowFocus: true,
    retry: 1,
  })
}

/**
 * Hook to download invoice receipt
 */
export const useDownloadStaffInvoice = () => {
  return useMutation<Blob, Error, string>({
    mutationFn: (invoiceId: string) => downloadStaffInvoice(invoiceId),
    onSuccess: (blob, invoiceId) => {
      // Create a download link and trigger download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `invoice-${invoiceId}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
  })
}

