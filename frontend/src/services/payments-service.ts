// src/services/payments-service.ts
import axiosInstance from '@/lib/api'

export interface PaymentCounts {
  total: number
  unbilled_visits: number
  pending_payment: number
  paid: number
}

export interface PaymentRow {
  id: number
  patientName: string
  contact: string
  service: string
  amount: number
  paymode: string
  receiptNo: string
  commission: number
  date: string
}

export const fetchPaymentCounts = async (): Promise<PaymentCounts> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/payments')
    return data.data
  } catch (error) {
    console.error('Failed to fetch counts:', error)
    throw error
  }
}

export const fetchPaymentHistory = async (): Promise<PaymentRow[]> => {
  try {
    const { data } = await axiosInstance.get('/v5/doctor/payment-history')
    return data.data
  } catch (error) {
    console.error('Failed to fetch payment history:', error)
    throw error
  }
}