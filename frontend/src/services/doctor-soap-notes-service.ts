import api from '@/lib/api'

export interface SoapNote {
  id: string
  appointment_id: string
  patient_id: string
  subjective: string
  objective: string
  assessment: string
  plan: string
  created_at: string
  updated_at: string
}

export interface CreateSoapNotePayload {
  appointment_id: string
  patient_id: string
  subjective: string
  objective: string
  assessment: string
  plan: string
}

export interface UpdateSoapNotePayload {
  subjective?: string
  objective?: string
  assessment?: string
  plan?: string
}

export interface SoapNotesResponse {
  success: boolean
  message: string
  data: {
    soap_notes: SoapNote[]
    pagination: {
      total: number
      page: number
      per_page: number
      total_pages: number
    }
  }
  errors: null | any
}

export interface SingleSoapNoteResponse {
  success: boolean
  message: string
  data: SoapNote
}

// Get all SOAP notes for a patient
export const getPatientSoapNotes = async (patientId: string): Promise<SoapNotesResponse> => {
  const { data } = await api.get<SoapNotesResponse>(`/v1/doctor/patients/${patientId}/soap-notes`)
  return data
}

// Get SOAP note by ID
export const getSoapNoteById = async (patientId: string, soapNoteId: string): Promise<SingleSoapNoteResponse> => {
  const { data } = await api.get<SingleSoapNoteResponse>(`/v1/doctor/patients/${patientId}/soap-notes/${soapNoteId}`)
  return data
}

// Get SOAP note by appointment ID
export const getSoapNoteByAppointmentId = async (patientId: string, appointmentId: string): Promise<SingleSoapNoteResponse> => {
  const { data } = await api.get<SingleSoapNoteResponse>(`/v1/doctor/patients/${patientId}/soap-notes/appointment/${appointmentId}`)
  return data
}

// Create SOAP note
export const createSoapNote = async (patientId: string, payload: CreateSoapNotePayload): Promise<SingleSoapNoteResponse> => {
  const { data } = await api.post<SingleSoapNoteResponse>(`/v1/doctor/patients/${patientId}/soap-notes`, payload)
  return data
}

// Update SOAP note
export const updateSoapNote = async (
  patientId: string,
  soapNoteId: string,
  payload: UpdateSoapNotePayload
): Promise<SingleSoapNoteResponse> => {
  const { data } = await api.put<SingleSoapNoteResponse>(`/v1/doctor/patients/${patientId}/soap-notes/${soapNoteId}`, payload)
  return data
}

