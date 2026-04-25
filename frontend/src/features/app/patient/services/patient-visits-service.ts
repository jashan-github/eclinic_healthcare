// src/services/patient-visits-service.ts
import api from '@/lib/api'

export interface VisitRecord {
  id: string
  title: string
  appointment_created_at: string
  appointment_start_time: string
  appointment_end_time: string
  check_status: string
  bookingId: string | null
  device_type: string | null
  notes: string
  precription_pdf_url: string | null
  digital_precription_pdf_url: string | null
  video_call_recordings: string[]
  assessment_summary: string | null
  appointment_date: {
    date: string
    day: string
    day_name: string
    month_name: string
    month: string
    year: string
  }
  soap_note: {
    id: string
  }
}

export interface PatientVisitsResponse {
  status: boolean
  message: string
  data: {
    records: VisitRecord[]
    skip: number
    limit: number
    total: number
  }
}

export interface RxTemplate {
  id: string
  doctor_id: string
  clinic_location_id: string
  clinic_location_name: string
  letterhead_image_path: string | null
  letterhead_image_url: string | null
  template_name: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface RxTemplatesResponse {
  status: boolean
  message: string
  data: {
    templates: RxTemplate[]
  }
}

export const fetchPatientVisits = async (patientId: string): Promise<PatientVisitsResponse> => {
  try {
    const response = await api.get<PatientVisitsResponse>(
      `/v1/doctor/patients/${patientId}/visits`
    )
    console.log('📡 Patient visits response:', response.data)
    return response.data
  } catch (error: any) {
    console.error(`Failed to fetch visits for patient: ${patientId}`, error)
    throw new Error(error.response?.data?.message || 'Failed to load patient visits')
  }
}

export const fetchRxTemplates = async (
): Promise<RxTemplatesResponse> => {
  try {
    const response = await api.get<RxTemplatesResponse>(
      `/v1/doctor/rx-templates`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch RX templates:', error)
    throw new Error(error.response?.data?.message || 'Failed to load RX templates')
  }
}