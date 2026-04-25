// src/hooks/use-appointment-payment.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  initializePayment,
  getPaymentStatus,
  verifyPayment,
  type InitializePaymentResponse,
  type PaymentStatusResponse,
  type VerifyPaymentResponse
} from '../service/appointment-payment-service'
import { toast } from 'react-toastify'

// Initialize payment
export const useInitializePayment = () => {
  return useMutation<InitializePaymentResponse, Error, string>({
    mutationFn: (appointmentRequestId: string) => initializePayment(appointmentRequestId),
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Payment initialized successfully')
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to initialize payment')
    }
  })
}

// Poll payment status
export const usePaymentStatus = (paymentId: string | null, enabled: boolean = false) => {
  return useQuery<PaymentStatusResponse, Error>({
    queryKey: ['paymentStatus', paymentId],
    queryFn: () => {
      if (!paymentId) throw new Error('Payment ID is required')
      return getPaymentStatus(paymentId)
    },
    enabled: !!paymentId && enabled,
    refetchInterval: (query) => {
      // Stop polling if payment is completed or failed
      const data = query.state.data
      if (data && data.data && (data.data.is_paid || ['FAILED', 'CANCELLED'].includes(data.data.status))) {
        return false
      }
      // Poll every 3 seconds
      return 3000
    },
    retry: false
  })
}

// Manually verify payment (fallback)
export const useVerifyPayment = () => {
  const queryClient = useQueryClient()
  
  return useMutation<VerifyPaymentResponse, Error, string>({
    mutationFn: (paymentId: string) => verifyPayment(paymentId),
    onSuccess: (data) => {
      if (data.success && data.data.is_paid) {
        toast.success('Payment verified successfully')
        queryClient.invalidateQueries({ queryKey: ['patientAppointments'] })
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message || 'Failed to verify payment')
    }
  })
}
