// src/services/patient-documents-service.ts
import api from '@/lib/api'

export interface Document {
  id: string
  patient_id: string
  document_type: string
  file_name: string
  file_path: string
  file_size: number
  file_size_mb: string
  file_extension: string
  mime_type: string
  issued_by: string | null
  issued_by_id: string | null
  issued_date: string | null
  uploaded_by: string
  notes: string | null
  download_url: string
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface DocumentsResponse {
  documents: Document[]
}

// Upload single document
export const uploadDocument = async (formData: FormData): Promise<Document> => {
  try {
    const response = await api.post('/v1/patient/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data.data
  } catch (error) {
    console.error('Upload failed:', error)
    throw error
  }
}

// Fetch documents with optional filters
export const fetchDocuments = async (filters?: {
  document_type?: string
  file_extension?: string
  issued_by?: string
}): Promise<DocumentsResponse> => {
  try {
    const response = await api.get('/v1/patient/documents', { params: filters })
    return response.data.data
  } catch (error) {
    console.error('Fetch documents failed:', error)
    throw error
  }
}

// Get single document details
export const fetchDocumentDetails = async (id: string): Promise<Document> => {
  try {
    const response = await api.get(`/v1/patient/documents/${id}`)
    return response.data.data
  } catch (error) {
    console.error('Fetch document details failed:', error)
    throw error
  }
}

// Delete document
export const deleteDocument = async (id: string): Promise<void> => {
  try {
    await api.delete(`/v1/patient/documents/${id}`)
  } catch (error) {
    console.error('Delete failed:', error)
    throw error
  }
}

// Download document (returns blob)
export const downloadDocument = async (id: string): Promise<Blob> => {
  try {
    const response = await api.get(`/v1/patient/documents/${id}/download`, {
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    console.error('Download failed:', error)
    throw error
  }
}