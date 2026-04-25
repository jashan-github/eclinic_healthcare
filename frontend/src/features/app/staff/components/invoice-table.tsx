// invoice-table.tsx

import { useState, useMemo } from 'react'
import { MagnifyingGlassIcon } from '@phosphor-icons/react'
import { Select, TextInput, Loader } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { useStaffInvoices } from '@/hooks/use-staff'
import SingleEntry from './single-entry-billing-status'

export default function InvoiceTable() {
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'All' | 'online' | 'cash'>('All')
  const [page, setPage] = useState(1)
  
  const [debouncedSearch] = useDebouncedValue(searchQuery, 500)

  // Build query params
  const queryParams = useMemo(() => {
    const params: any = {
      page,
      per_page: 20,
    }
    
    if (debouncedSearch) {
      params.search = debouncedSearch
    }
    
    if (typeFilter !== 'All') {
      params.payment_method = typeFilter
    }
    
    return params
  }, [debouncedSearch, typeFilter, page])

  const { data: invoicesData, isLoading, isError } = useStaffInvoices(queryParams)

  const invoices = invoicesData?.data?.invoices || []
  const pagination = invoicesData?.data?.pagination

  return (
    <div className="h-full flex flex-col">
      {/* Search */}
      <div className="flex gap-4 mb-6 flex-shrink-0">
        <TextInput
          placeholder="Search by patient name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          leftSection={<MagnifyingGlassIcon size={18} weight="bold" />}
          className="flex-1"
          radius="md"
          size="md"
        />
        <Select
          placeholder="Filter by type"
          value={typeFilter}
          onChange={(value) => setTypeFilter((value as 'All' | 'online' | 'cash') || 'All')}
          data={[
            { value: 'All', label: 'All Entries' },
            { value: 'online', label: 'Online' },
            { value: 'cash', label: 'Cash' },
          ]}
          radius="md"
          size="md"
          className="w-64"
        />
      </div>

      {/* Scrollable List */}
      <div className="flex-1 overflow-y-auto space-y-4 px-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader size="md" />
          </div>
        ) : isError ? (
          <div className="text-center py-20 text-red-500 font-medium h-full flex items-center justify-center">
            Failed to load invoices
          </div>
        ) : invoices.length > 0 ? (
          <div className="min-h-full">
            {invoices.map((inv) => (
              <SingleEntry
                key={inv.id}
                invoiceId={inv.id}
                name={inv.patient_name}
                email={inv.patient_email || ''}
                amount={inv.amount}
                currency={inv.currency}
                paymentDate={inv.payment_date || inv.created_at}
                paymentMethod={inv.payment_method === 'online' ? 'Online' : inv.payment_method === 'cash' ? 'Cash' : undefined}
                contactNumber={inv.patient_phone || 'N/A'}
                emergencyContact="N/A"
                familyContact="N/A"
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 text-gray-500 font-medium h-full flex items-center justify-center">
            {searchQuery ? 'No invoices match your search' : 'No invoices found'}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600 font-poppins">
            Showing {pagination.page === 1 ? 1 : (pagination.page - 1) * pagination.per_page + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} invoices
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={pagination.page === 1}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700 font-poppins px-3">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
              disabled={pagination.page >= pagination.total_pages}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}

    </div>
  )
}
