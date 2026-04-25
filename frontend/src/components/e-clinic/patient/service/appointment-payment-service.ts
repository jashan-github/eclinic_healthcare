// src/services/appointment-payment-service.ts
import api from '@/lib/api'

// Initialize Payment Response
export interface InitializePaymentResponse {
  success: boolean
  message: string
  data: {
    payment_id: string
    sentoo_payment_id: string
    payment_url: string
    qr_code: string | null
    amount: number
    currency: string
    status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  }
  errors: any | null
}

// Payment Status Response
export interface PaymentStatusResponse {
  success: boolean
  message: string
  data: {
    payment_id: string
    sentoo_payment_id: string
    status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
    is_paid: boolean
    appointment_id: string | null
    appointment_confirmed: boolean
    amount: number
    currency: string
  }
  errors: any | null
}

// Verify Payment Response
export interface VerifyPaymentResponse {
  success: boolean
  message: string
  data: {
    status: 'success' | 'pending' | 'already_completed'
    payment_status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
    is_paid: boolean
    appointment_id: string | null
    message: string
  }
  errors: any | null
}

// Initialize payment for an appointment
export const initializePayment = async (appointmentRequestId: string): Promise<InitializePaymentResponse> => {
  const response = await api.post(`/v1/patient/appointments/${appointmentRequestId}/pay`)
  return response.data
}

// Get payment status (for polling)
export const getPaymentStatus = async (paymentId: string): Promise<PaymentStatusResponse> => {
  const response = await api.get(`/v1/patient/appointments/payment-status/${paymentId}`)
  return response.data
}

// Manually verify payment (fallback)
export const verifyPayment = async (paymentId: string): Promise<VerifyPaymentResponse> => {
  const response = await api.post(`/v1/patient/appointments/verify-payment/${paymentId}`)
  return response.data
}