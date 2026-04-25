import PaymentFilters from '@/features/app/payments/components/payment-filters'
import PaymentsHeader from '@/features/app/payments/components/payments-header'
import PaymentsTablePreHeader from '@/features/app/payments/components/payments-table-pre-header'
import { useDoctorPayments } from '@/features/app/payments/hooks/use-payment'
import { useHeaderStore } from '@/store/use-header-store'
import { useEffect, useState, type FC, type ReactElement } from 'react'

const PaymentsPage: FC = (): ReactElement => {
  const { setRightContent } = useHeaderStore()
  const [page, setPage] = useState(1)
  const [dateFilter, setDateFilter] = useState<'week' | 'month' | 'custom'>('week')
  const [customDates, setCustomDates] = useState({ from: '', to: '' })

  const { data, isLoading, error } = useDoctorPayments({
    page,
    perPage: 20,
    period: dateFilter,
    dateFrom: dateFilter === 'custom' ? customDates.from : undefined,
    dateTo: dateFilter === 'custom' ? customDates.to : undefined,
  })

  useEffect(() => {
    setRightContent(PaymentsHeader)
    return () => {
      setRightContent(null)
    }
  }, [setRightContent])

  return (
    <div className="bg-white flex flex-col gap-6 p-4 overflow-auto">
      <PaymentFilters stats={data?.stats} />
      <div className="flex flex-col">
        <PaymentsTablePreHeader 
          data={data}
          isLoading={isLoading}
          error={error}
          page={page}
          setPage={setPage}
          dateFilter={dateFilter}
          setDateFilter={setDateFilter}
          customDates={customDates}
          setCustomDates={setCustomDates}
        />
      </div>
    </div>
  )
}

export default PaymentsPage