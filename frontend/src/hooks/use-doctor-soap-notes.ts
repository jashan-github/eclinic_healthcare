import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPatientSoapNotes,
  getSoapNoteById,
  getSoapNoteByAppointmentId,
  createSoapNote,
  updateSoapNote,
  type SoapNotesResponse,
  type SingleSoapNoteResponse,
  type CreateSoapNotePayload,
  type UpdateSoapNotePayload
} from '@/services/doctor-soap-notes-service'
import { toast } from 'react-toastify'

// Get all SOAP notes for a patient
export const usePatientSoapNotes = (patientId: string) => {
  return useQuery<SoapNotesResponse, Error>({
    queryKey: ['patientSoapNotes', patientId],
    queryFn: () => getPatientSoapNotes(patientId),
    enabled: !!patientId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Get SOAP note by ID
export const useSoapNoteById = (patientId: string, soapNoteId: string, enabled: boolean = true) => {
  return useQuery<SingleSoapNoteResponse, Error>({
    queryKey: ['soapNote', patientId, soapNoteId],
    queryFn: () => getSoapNoteById(patientId, soapNoteId),
    enabled: !!patientId && !!soapNoteId && enabled,
    staleTime: 1000 * 60 * 5,
  })
}

// Get SOAP note by appointment ID
export const useSoapNoteByAppointmentId = (patientId: string, appointmentId: string, enabled: boolean = true) => {
  return useQuery<SingleSoapNoteResponse, Error>({
    queryKey: ['soapNoteByAppointment', patientId, appointmentId],
    queryFn: () => getSoapNoteByAppointmentId(patientId, appointmentId),
    enabled: !!patientId && !!appointmentId && enabled,
    staleTime: 1000 * 60 * 5,
  })
}

// Create SOAP note
export const useCreateSoapNote = () => {
  const queryClient = useQueryClient()
  
  return useMutation<SingleSoapNoteResponse, Error, { patientId: string; payload: CreateSoapNotePayload }>({
    mutationFn: ({ patientId, payload }) => createSoapNote(patientId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['patientSoapNotes', variables.patientId] })
      toast.success('SOAP note created successfully!')
    },
    onError: (error: any) => {
      // Check for specific API error messages
      if (error?.response?.data?.message) {
        toast.error(error.response.data.message)
      } else if (error?.response?.data?.errors?.appointment_id) {
        // Handle appointment_id specific errors
        const appointmentErrors = error.response.data.errors.appointment_id
        if (Array.isArray(appointmentErrors)) {
          toast.error(appointmentErrors[0])
        } else {
          toast.error(appointmentErrors)
        }
      } else {
        toast.error(error.message || 'Failed to create SOAP note')
      }
    },
  })
}

// Update SOAP note
export const useUpdateSoapNote = () => {
  const queryClient = useQueryClient()
  
  return useMutation<
    SingleSoapNoteResponse,
    Error,
    { patientId: string; soapNoteId: string; payload: UpdateSoapNotePayload }
  >({
    mutationFn: ({ patientId, soapNoteId, payload }) => updateSoapNote(patientId, soapNoteId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['patientSoapNotes', variables.patientId] })
      queryClient.invalidateQueries({ queryKey: ['soapNote', variables.patientId, variables.soapNoteId] })
      toast.success('SOAP note updated successfully!')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update SOAP note')
    },
  })
}

