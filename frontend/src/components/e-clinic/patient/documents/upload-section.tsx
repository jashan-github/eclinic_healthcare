// upload-section.tsx - Dynamic with API hooks
import { ArrowUpIcon } from '@phosphor-icons/react'
import { useState, useRef, useEffect } from 'react'
import { toast } from 'react-toastify'
import { useUploadDocument } from '../hook/use-patient-documents'

const UploadSection = () => {
  const [documentType, setDocumentType] = useState('')
  const [issuedBy, setIssuedBy] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const uploadMutation = useUploadDocument()

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(e.type === 'dragenter' || e.type === 'dragover')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files[0]?.type.startsWith('image/')) {
      const file = e.dataTransfer.files[0]
      setSelectedImage(file)
      setPreviewUrl(URL.createObjectURL(file))
    } else {
      toast.error('Only image files allowed')
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file?.type.startsWith('image/')) {
      setSelectedImage(file)
      setPreviewUrl(URL.createObjectURL(file))
    } else {
      toast.error('Only image files allowed')
    }
  }

  const handleUpload = () => {
    if (!selectedImage || !documentType) {
      toast.error('Please select an image and enter document type')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedImage)
    formData.append('document_type', documentType)
    formData.append('issued_by', issuedBy)
    formData.append('issued_date', '')
    formData.append('notes', '')

    uploadMutation.mutate(formData, {
      onSuccess: () => {
        setSelectedImage(null)
        if (previewUrl) URL.revokeObjectURL(previewUrl)
        setPreviewUrl(null)
        setDocumentType('')
        setIssuedBy('')
        toast.success('Document uploaded successfully')
      },
      onError: () => {
        toast.error('Failed to upload document')
      }
    })
  }

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6 mb-6">
      <h2 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-6">
        Upload Report
      </h2>

      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
          dragActive ? 'border-[#002FD4] bg-[#F4F6F9]' : 'border-[#E4E5ED]'
        }`}
        onClick={() => fileInputRef.current?.click()}
      >
        {previewUrl ? (
          <img src={previewUrl} alt="Preview" className="mx-auto max-h-64 rounded" />
        ) : (
          <>
            <ArrowUpIcon size={48} className="mx-auto text-[#002FD4] mb-4" />
            <p className="font-poppins font-medium text-[14px]">
              Drag & drop or <span className="text-[#002FD4]">browse</span>
            </p>
            <p className="font-poppins text-[13px] text-gray-500 mt-2">JPG, PNG only</p>
          </>
        )}
        <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileInput} className="hidden" />
      </div>

      <div className="grid grid-cols-2 gap-6 mt-6">
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Document Type
          </label>
          <input
            type="text"
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            placeholder="e.g. Blood Test Report"
            className="w-full px-4 py-2.5 border border-[#E4E1FA] rounded-md font-poppins text-[14px] focus:outline-none focus:ring-2 focus:ring-[#E4E1FA]"
          />
        </div>
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Issued By
          </label>
          <input
            type="text"
            value={issuedBy}
            onChange={(e) => setIssuedBy(e.target.value)}
            placeholder="e.g. Dr. Sara"
            className="w-full px-4 py-2.5 border border-[#E4E1FA] rounded-md font-poppins text-[14px] focus:outline-none focus:ring-2 focus:ring-[#E4E1FA]"
          />
        </div>
      </div>

      <div className="mt-6 text-right">
        <button
          onClick={handleUpload}
          disabled={uploadMutation.isPending || !selectedImage}
          className="bg-[#002FD4] hover:bg-[#001FB8] text-white px-6 py-2.5 rounded-md font-poppins font-semibold text-[14px] disabled:opacity-50 transition-colors"
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
        </button>
      </div>
    </div>
  )
}

export default UploadSection