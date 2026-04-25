// filter-section.tsx - Dynamic with controlled state
import { useState } from 'react'

interface FilterSectionProps {
  onFilterChange: (filters: {
    document_type: string
    file_extension: string
    issued_by: string
  }) => void
}

const FilterSection = ({ onFilterChange }: FilterSectionProps) => {
  // Temporary filters (form inputs) - only applied on button click
  const [tempFilters, setTempFilters] = useState({
    document_type: '',
    file_extension: '',
    issued_by: ''
  })

  const documentTypes = ['Blood Test Report', 'X-Ray', 'Lab Results', 'Prescription', 'Medical Certificate']
  const fileFormats = ['PDF', 'JPG', 'PNG', 'DOC', 'DOCX']

  const handleApplyFilters = () => {
    // Only send filters to parent when Apply is clicked
    onFilterChange(tempFilters)
  }

  const handleClearFilters = () => {
    const emptyFilters = {
      document_type: '',
      file_extension: '',
      issued_by: ''
    }
    setTempFilters(emptyFilters)
    onFilterChange(emptyFilters)
  }

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6 mb-6">
      <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4">
        Filter Documents
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Document Type
          </label>
          <select
            value={tempFilters.document_type}
            onChange={(e) => setTempFilters({ ...tempFilters, document_type: e.target.value })}
            className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
              font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
              focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
          >
            <option value="">All</option>
            {documentTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            File Format
          </label>
          <select
            value={tempFilters.file_extension}
            onChange={(e) => setTempFilters({ ...tempFilters, file_extension: e.target.value })}
            className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
              font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
              focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
          >
            <option value="">All</option>
            {fileFormats.map((format) => (
              <option key={format} value={format.toLowerCase()}>
                {format}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Issued By
          </label>
          <input
            type="text"
            value={tempFilters.issued_by}
            onChange={(e) => setTempFilters({ ...tempFilters, issued_by: e.target.value })}
            placeholder="Enter doctor name"
            className="w-full px-4 py-2.5 rounded-md border border-[#E4E1FA] 
              font-poppins text-[14px] font-normal text-[#0F1011] leading-[20px]
              focus:outline-none focus:ring-2 focus:ring-[#E4E1FA] transition-all"
          />
        </div>
        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={handleClearFilters}
            className="flex-1 bg-white border border-[#E4E5ED] hover:bg-[#F4F6F9] text-[#0F1011] font-poppins font-semibold 
              text-[14px] leading-[20px] py-2.5 px-4 rounded-md transition-colors"
          >
            Clear
          </button>
          <button
            type="button"
            onClick={handleApplyFilters}
            className="flex-1 bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
              text-[14px] leading-[20px] py-2.5 px-4 rounded-md transition-colors"
          >
            Apply
          </button>
        </div>
      </div>
    </div>
  )
}

export default FilterSection