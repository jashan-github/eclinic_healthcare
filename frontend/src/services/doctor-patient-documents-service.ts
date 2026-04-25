import api from '@/lib/api'

export interface PatientDocument {
  id: string
  document_type: string
  file_name: string
  file_url: string
  file_size: number
  file_extension: string
  mime_type: string
  issued_by: string | null
  issued_date: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface PatientDocumentsResponse {
  success: boolean
  message: string
  data: {
    documents: PatientDocument[]
    pagination: {
      total: number
      page: number
      per_page: number
      total_pages: number
    }
  }
  errors: null | any
}

export interface GetPatientDocumentsParams {
  document_type?: string
  page?: number
  per_page?: number
}

export const getPatientDocuments = async (
  patientId: string,
  params?: GetPatientDocumentsParams
): Promise<PatientDocumentsResponse> => {
  const { data } = await api.get<PatientDocumentsResponse>(
    `/v1/doctor/patients/${patientId}/documents`,
    {
      params: {
        document_type: params?.document_type,
        page: params?.page || 1,
        per_page: params?.per_page || 20
      }
    }
  )
  return data
}

