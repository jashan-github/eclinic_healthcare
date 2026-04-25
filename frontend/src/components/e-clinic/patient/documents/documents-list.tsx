// documents-list.tsx - Dynamic with API data
import { EyeIcon, DownloadIcon, TrashIcon, FileIcon, ImageIcon, XIcon } from '@phosphor-icons/react'
import { useState } from 'react'
import { useDocumentDetails, useDeleteDocument, useDownloadDocument } from '../hook/use-patient-documents'
import { toast } from 'react-toastify'
import { formatDate, formatTime } from '@/utils/helper'

interface Document {
  id: string
  document_type: string
  file_name: string
  file_extension: string
  created_at: string
  issued_by: string | null
  file_size_mb: string
}

interface DocumentsListProps {
  documents: Document[]
  isLoading: boolean
}

const DocumentsList = ({ documents, isLoading }: DocumentsListProps) => {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const { data: docDetails } = useDocumentDetails(selectedDocId || '', !!selectedDocId && modalOpen)
  const deleteMutation = useDeleteDocument()
  const downloadMutation = useDownloadDocument()

  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [docToDelete, setDocToDelete] = useState<Document | null>(null)

  const getFileIcon = (fileExtension: string) => {
    if (['jpg', 'jpeg', 'png', 'gif'].includes(fileExtension.toLowerCase())) {
      return <ImageIcon size={24} weight="bold" className="text-[#002FD4]" />
    }
    return <FileIcon size={24} weight="bold" className="text-[#002FD4]" />
  }

  const openDetails = (id: string) => {
    setSelectedDocId(id)
    setModalOpen(true)
  }

  const openDeleteConfirm = (doc: Document) => {
    setDocToDelete(doc)
    setDeleteModalOpen(true)
  }

  const confirmDelete = () => {
    if (docToDelete) {
      deleteMutation.mutate(docToDelete.id, {
        onSuccess: () => {
        },
        onError: () => {
          toast.error('Failed to delete document')
        },
      })
    }
    setDeleteModalOpen(false)
    setDocToDelete(null)
  }

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      setModalOpen(false)
      setDeleteModalOpen(false)
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
        <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
          All Documents
        </h3>
        <div className="text-center py-12">
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
            Loading documents...
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
        <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
          All Documents
        </h3>
        <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-6">
          View and download your files
        </p>

        {documents.length === 0 ? (
          <div className="text-center py-12">
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
              No documents found
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((document) => (
              <div
                key={document.id}
                className="flex items-center gap-4 p-4 border border-[#E4E5ED] rounded-lg hover:bg-[#F4F6F9] transition-colors"
              >
                {/* File Icon */}
                {getFileIcon(document.file_extension)}

                {/* File Info */}
                <div className="flex-1">
                  <p className="font-poppins font-medium text-[14px] leading-[20px] text-[#0F1011]">
                    {document.document_type}
                  </p>
                  <p className="font-poppins font-normal text-[12px] leading-[16px] text-[#64748B]">
                    {document.file_name} • {formatDate(document.created_at.split(' ')[0])}{' '}{formatTime(document.created_at.split(' ')[1])}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-4">
                  <EyeIcon
                    size={20}
                    className="cursor-pointer text-[#002FD4] hover:text-[#001FB8]"
                    onClick={() => openDetails(document.id)}
                  />
                  <DownloadIcon
                    size={20}
                    className="cursor-pointer text-[#002FD4] hover:text-[#001FB8]"
                    onClick={() => downloadMutation.mutate(document.id)}
                  />
                  <TrashIcon
                    size={20}
                    className="cursor-pointer text-[#DC2626] hover:text-[#B91C1C]"
                    onClick={() => openDeleteConfirm(document)}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Details Modal - Custom div with original styling */}
      {modalOpen && (
        <div
        className="fixed inset-0 bg-black/20 bg-opacity-10 z-50 flex items-center justify-center p-4"
        onClick={handleBackdropClick}
        >
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011]">
                Document Details
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="hover:text-[#0F1011] hover:cursor-pointer text-[34px] leading-none"
              >
                <XIcon color='#64748B' />
              </button>
            </div>

            {docDetails && (
              <>
                <div className="space-y-4 mb-6">
                  <div>
                    <p className="font-poppins font-medium text-[13px] leading-[20px] text-[#64748B]">
                      Type
                    </p>
                    <p className="font-poppins text-[14px] leading-[20px] text-[#0F1011]">
                      {docDetails.document_type}
                    </p>
                  </div>
                  <div>
                    <p className="font-poppins font-medium text-[13px] leading-[20px] text-[#64748B]">
                      File Name
                    </p>
                    <p className="font-poppins text-[14px] leading-[20px] text-[#0F1011]">
                      {docDetails.file_name}
                    </p>
                  </div>
                  <div>
                    <p className="font-poppins font-medium text-[13px] leading-[20px] text-[#64748B]">
                      Size
                    </p>
                    <p className="font-poppins text-[14px] leading-[20px] text-[#0F1011]">
                      {docDetails.file_size_mb} MB
                    </p>
                  </div>
                  <div>
                    <p className="font-poppins font-medium text-[13px] leading-[20px] text-[#64748B]">
                      Issued By
                    </p>
                    <p className="font-poppins text-[14px] leading-[20px] text-[#0F1011]">
                      {docDetails.issued_by || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="font-poppins font-medium text-[13px] leading-[20px] text-[#64748B]">
                      Uploaded
                    </p>
                    <p className="font-poppins text-[14px] leading-[20px] text-[#0F1011]">
                      {docDetails.created_at}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => downloadMutation.mutate(docDetails.id)}
                  disabled={downloadMutation.isPending}
                  className="w-full bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors disabled:opacity-50"
                >
                  {downloadMutation.isPending ? 'Downloading...' : 'Download Document'}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Delete Confirmation Popup - Custom div with original styling */}
      {deleteModalOpen && (
        <div
        className="fixed inset-0 bg-black/20 bg-opacity-40 z-50 flex items-center justify-center p-4"
        onClick={handleBackdropClick}
        >
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011]">
                Confirm Delete
              </h3>
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="text-[#64748B] hover:text-[#0F1011] text-[24px] leading-none"
              >
                ×
              </button>
            </div>

            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011] mb-6">
              Are you sure you want to delete <strong>{docToDelete?.file_name}</strong>?
            </p>

            <div className="flex justify-end gap-4">
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="px-6 py-2.5 border border-[#E4E5ED] rounded-md font-poppins font-medium text-[14px] text-[#0F1011] hover:bg-[#F4F6F9] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleteMutation.isPending}
                className="px-6 py-2.5 bg-[#DC2626] hover:bg-[#B91C1C] text-white font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Yes, Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default DocumentsList