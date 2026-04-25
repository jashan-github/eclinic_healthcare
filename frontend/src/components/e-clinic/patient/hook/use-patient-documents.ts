// src/hooks/use-patient-documents.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  uploadDocument,
  fetchDocuments,
  fetchDocumentDetails,
  deleteDocument,
  downloadDocument,
  type Document,
  type DocumentsResponse
} from '../service/patient-documents-service'
import { toast } from 'react-toastify'

export const useDocuments = (filters = {}) => {
  return useQuery<DocumentsResponse>({
    queryKey: ['patient-documents', filters],
    queryFn: () => fetchDocuments(filters),
    staleTime: 5 * 60 * 1000,
  })
}

export const useUploadDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      toast.success('Document uploaded successfully!')
      queryClient.invalidateQueries({ queryKey: ['patient-documents'] })
    },
    onError: () => toast.error('Failed to upload document')
  })
}

export const useDocumentDetails = (id: string, enabled = true) => {
  return useQuery<Document>({
    queryKey: ['patient-document', id],
    queryFn: () => fetchDocumentDetails(id),
    enabled: enabled && !!id,
  })
}

export const useDeleteDocument = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      toast.success('Document deleted successfully!')
      queryClient.invalidateQueries({ queryKey: ['patient-documents'] })
    },
    onError: () => toast.error('Failed to delete document')
  })
}

export const useDownloadDocument = () => {
  return useMutation({
    mutationFn: downloadDocument,
    onSuccess: (blob, variables) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `document_${variables}.png` // or extract name from backend later
      a.click()
      window.URL.revokeObjectURL(url)
    },
    onError: () => toast.error('Failed to download document')
  })
}