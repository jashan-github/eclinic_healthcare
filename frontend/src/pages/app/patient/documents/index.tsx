// index.tsx - Main page with dynamic data from API
import { useState, useEffect } from 'react'
import UploadSection from '@/components/e-clinic/patient/documents/upload-section'
import FilterSection from '@/components/e-clinic/patient/documents/filter-section'
import DocumentsList from '@/components/e-clinic/patient/documents/documents-list'
import { useHeaderStore } from '@/store/use-header-store'
import { useDocuments } from '@/components/e-clinic/patient/hook/use-patient-documents'

const PatientDocumentsPage = () => {
  const { setPageTitle } = useHeaderStore()

  useEffect(() => {
    setPageTitle('My Documents')
  }, [setPageTitle])

  // Applied filters state that hits the backend
  const [appliedFilters, setAppliedFilters] = useState({
    document_type: '',
    file_extension: '',
    issued_by: ''
  })

  // Fetch documents from API with applied filters
  const { data, isLoading } = useDocuments(appliedFilters)
  const documents = data?.documents || []

  // Handle filter changes from FilterSection
  const handleFilterChange = (newFilters: {
    document_type: string
    file_extension: string
    issued_by: string
  }) => {
    setAppliedFilters(newFilters)
  }

  return (
    <div className="h-screen overflow-y-auto bg-[#F4F6F9]">
      <div className="p-6">
        <UploadSection />
        <FilterSection onFilterChange={handleFilterChange} />
        <DocumentsList documents={documents} isLoading={isLoading} />
      </div>
    </div>
  )
}

export default PatientDocumentsPage