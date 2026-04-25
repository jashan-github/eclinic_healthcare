import { useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import {
  CaretDownIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
} from '@phosphor-icons/react'
import { Button } from '@mantine/core'
import { formatFee } from '@/utils/helper'
import type { DoctorPaymentsResponse } from '../services/payments-service'
import { useDownloadStaffInvoice } from '@/hooks/use-staff'
import { toast } from 'react-toastify'

interface PaymentsTablePreHeaderProps {
  data?: DoctorPaymentsResponse
  isLoading: boolean
  error: Error | null
  page: number
  setPage: (page: number | ((prev: number) => number)) => void
  dateFilter: 'week' | 'month' | 'custom'
  setDateFilter: (filter: 'week' | 'month' | 'custom') => void
  customDates: { from: string; to: string }
  setCustomDates: (dates: { from: string; to: string } | ((prev: { from: string; to: string }) => { from: string; to: string })) => void
}

export default function PaymentHistory({
  data,
  isLoading,
  error,
  page,
  setPage,
  dateFilter,
  setDateFilter,
  customDates,
  setCustomDates
}: PaymentsTablePreHeaderProps) {
  const [search, setSearch] = useState('')
  const [paymode, setPaymode] = useState('all')
  const [service, setService] = useState('all')
  const [showCustomPicker, setShowCustomPicker] = useState(false)
  const [isCustomMode, setIsCustomMode] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const downloadMutation = useDownloadStaffInvoice()

  const handleDownloadInvoice = (invoiceId: string) => {
    downloadMutation.mutate(invoiceId, {
      onSuccess: () => {
        toast.success('Invoice downloaded successfully')
      },
      onError: (error: any) => {
        toast.error(error?.message || 'Failed to download invoice')
      }
    })
  }

  const transactions = data?.transactions ?? []
  const pagination = data?.pagination
  const stats = data?.stats

  const filteredRows = useMemo(() => {
    return transactions.filter((row) => {
      const patientName = row.patient_details?.name?.toLowerCase()
      const serviceName = row.service?.name?.toLowerCase()

      const matchesSearch =
        patientName.includes(search.toLowerCase())

      const matchesPaymode = paymode === 'all' || row.paymode === paymode
      const matchesService = service === 'all' || serviceName === service.toLowerCase()

      return matchesSearch && matchesPaymode && matchesService
    })
  }, [transactions, search, paymode, service])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowCustomPicker(false)
        // Don't reset isCustomMode here - let it persist
      }
    }

    if (showCustomPicker) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCustomPicker])

  // For dropdown options
  const paymodeOptions = ['all', ...new Set(transactions.map(r => r.paymode))]
  const serviceOptions = ['all', ...new Set(transactions.map(r => r.service.name))]

  if (isLoading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Loading payment history...
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-600">
        Failed to load payments: {error.message}
      </div>
    )
  }

  return (
    <div className="w-full overflow-auto">
      {/* Header + Stats (optional - you can show total_earned here) */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="font-poppins font-medium text-xl leading-7 text-black">
            Payment History
          </h2>
          {stats && (
            <p className="text-sm text-gray-600 mt-1">
              Total Earned: {formatFee(stats.total_earned, stats.currency)}
              {stats.growth > 0 && ` (+${stats.growth}% growth)`}
            </p>
          )}
        </div>

        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowCustomPicker(!showCustomPicker)}
            className="flex w-[138px] h-9 items-center justify-between gap-2 rounded-lg bg-[#F4F4F4] px-3 py-2 transition-all hover:bg-[#E8E8E8]"
          >
            <FunnelIcon weight="bold" className="h-4 w-4 text-[#0F1011]" />
            <span className="font-poppins font-bold text-[13px] leading-4 text-[#0F1011]">
              {isCustomMode || dateFilter === 'custom' ? 'Custom' :
                dateFilter === 'week' ? 'This Week' : 'This Month'}
            </span>
            <CaretDownIcon className="h-4 w-4 text-[#0F1011]" />
          </button>

          {showCustomPicker && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-10">
              <div className="space-y-3">
                <button
                  onClick={() => {
                    setDateFilter('week')
                    setIsCustomMode(false)
                    setShowCustomPicker(false)
                  }}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded hover:bg-gray-100",
                    dateFilter === 'week' && !isCustomMode && 'bg-gray-100 font-medium'
                  )}
                >
                  This Week
                </button>
                <button
                  onClick={() => {
                    setDateFilter('month')
                    setIsCustomMode(false)
                    setShowCustomPicker(false)
                  }}
                  className={cn(
                    "w-full text-left px-3 py-2 rounded hover:bg-gray-100",
                    dateFilter === 'month' && !isCustomMode && 'bg-gray-100 font-medium'
                  )}
                >
                  This Month
                </button>
                <button
                  onClick={() => setIsCustomMode(true)} // Just toggle UI, don't change dateFilter
                  className={cn(
                    "w-full text-left px-3 py-2 rounded hover:bg-gray-100",
                    isCustomMode && 'bg-gray-100 font-medium'
                  )}
                >
                  Custom Range
                </button>

                {isCustomMode && (
                  <div className="pt-3 border-t space-y-2">
                    <input
                      type="date"
                      value={customDates.from}
                      onChange={(e) => setCustomDates(prev => ({ ...prev, from: e.target.value }))}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    />
                    <input
                      type="date"
                      value={customDates.to}
                      onChange={(e) => setCustomDates(prev => ({ ...prev, to: e.target.value }))}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        fullWidth
                        onClick={() => {
                          setCustomDates({ from: '', to: '' })
                          // setIsCustomMode(false)
                        }}
                      >
                        Clear
                      </Button>
                      <Button
                        size="sm"
                        fullWidth
                        onClick={() => {
                          setDateFilter('custom')
                          setShowCustomPicker(false)
                        }}
                        disabled={!customDates.from || !customDates.to}
                      >
                        Apply
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap justify-between items-center gap-4 rounded-t-lg bg-[#F4F6F9] p-4">
        <div className="relative flex-1 max-w-[360px]">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by Phone / Name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white pl-10 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <select
            value={paymode}
            onChange={(e) => setPaymode(e.target.value)}
            className="rounded-md border w-[196px] border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {paymodeOptions.map(opt => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'Paymode' : opt}
              </option>
            ))}
          </select>

          <select
            value={service}
            onChange={(e) => setService(e.target.value)}
            className="rounded-md border w-[196px] border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {serviceOptions.map(opt => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'Service' : opt}
              </option>
            ))}
          </select>

          {/* <Button size="sm" variant="subtle">
            Download Report
          </Button> */}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-auto rounded-b-lg border border-[#E4E5ED] bg-white">
        <table className="min-w-full">
          <thead>
            <tr>
              {[
                'S.NO',
                'PATIENT DETAILS',
                'CONTACT NUMBER',
                'SERVICE',
                'AMOUNT',
                'PAYMODE',
                'RECEIPT #',
                'TOTAL COMMISSION',
                'ACTIONS'
              ].map((header, idx, arr) => (
                <th
                  key={header}
                  className="px-6 py-4 font-poppins font-bold text-[11px] leading-4 uppercase text-[#0F1011] text-center"
                  style={{
                    borderBottom: '2px solid #E5E7EB',
                    borderLeft: idx === 0 ? 'none' : '1px solid #E5E7EB',
                    borderRight: idx === arr.length - 1 ? 'none' : '1px solid #E5E7EB'
                  }}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredRows.length === 0 ? (
              <tr>
                <td
                  colSpan={9}
                  className="px-6 py-12 text-center font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011]"
                >
                  No records found.
                </td>
              </tr>
            ) : (
              filteredRows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 transition-colors"
                >
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011] tabular-nums">
                      {row.serial_number}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011]">
                      {row.patient_details.name}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011]">
                      {row.contact_number}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011]">
                      {row.service.name}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011] tabular-nums">
                      {formatFee(row.amount, row.currency)}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span
                      className={cn(
                        'inline-flex rounded-full px-2.5 py-1 text-xs font-medium',
                        row.paymode === 'COMPLETED' && 'bg-green-100 text-green-800',
                        // add more paymode styles as needed
                      )}
                    >
                      {row.paymode}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011]">
                      {row.receipt_number}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <span className="font-poppins font-normal text-[11px] leading-4 uppercase text-[#0F1011] tabular-nums">
                      {/* If you have commission field later — for now placeholder */}
                      —
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-center">
                    <div
                      onClick={() => !downloadMutation.isPending && handleDownloadInvoice(row.id)}
                      className={`w-full transition-colors hover:cursor-pointer`}
                    >
                      <span className={`font-poppins text-sm font-medium leading-5 text-center block underline text-slate-600`}>
                        View Invoice
                      </span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Simple Pagination */}
        {pagination && pagination.total > 0 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              Showing {filteredRows.length} of {pagination.total} transactions
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="xs"
                variant="outline"
                disabled={page === 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </Button>
              <span className="text-sm font-medium">
                Page {page} of {pagination.total_pages}
              </span>
              <Button
                size="xs"
                variant="outline"
                disabled={page >= pagination.total_pages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}