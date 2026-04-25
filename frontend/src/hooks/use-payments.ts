// src/hooks/use-payments.ts
import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import {
  fetchPaymentCounts,
  type PaymentCounts,
  fetchPaymentHistory,
} from '@/services/payments-service'

export const usePaymentCounts = (): UseQueryResult<PaymentCounts, Error> => {
  return useQuery<PaymentCounts, Error>({
    queryKey: ['paymentCounts'],
    queryFn: fetchPaymentCounts,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}

export const usePaymentHistory = () => {
  return useQuery({
    queryKey: ['paymentHistory'],
    queryFn: async () => {
      const rows = await fetchPaymentHistory()
      return rows.map((row) => ({
        ...row,
        date: new Date(row.date),
      }))
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}