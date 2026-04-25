// src/services/analytics.ts
import api from '@/lib/api'

export interface AnalyticsOverview {
  total: number
  total_appointments: number
  revenue: number
  waiver: number
}

export interface MonthlyPerformance {
  year: number
  month: number
  month_label: string
  appointments: number
  revenue: number
}

export interface TopMedicalMetrics {
  top_symptom: string
  top_diagnosis: string
  top_lab_test: string
  top_drug: string
}

export interface PaymentBreakdown {
  total_payment: number
  total_cash_payment: number
  total_online_payment: number
  currency: string
}

export interface AnalyticsReport {
  summary: {
    total_patients: number
    total_appointments: number
    revenue: number
    total_waiver: number
    currency: string
  }
  monthly_performance: MonthlyPerformance[]
  top_medical_metrics: TopMedicalMetrics
  payment_breakdown: PaymentBreakdown
}

export const fetchAnalyticsOverview = async (): Promise<AnalyticsOverview> => {
  try {
    const response = await api.get(`/analytics/overview`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch analytics overview:', error)
    throw new Error('Unable to load analytics data')
  }
}

export const fetchAnalyticsSummary = async (): Promise<String> => {
  try {
    const response = await api.get(`/analytics/summary`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch analytics overview:', error)
    throw new Error('Unable to load analytics data')
  }
}

export const fetchAnalyticsReport = async (): Promise<AnalyticsReport> => {
  try {
    const response = await api.get(`/v1/doctor/analytics/report`, {
      headers: { accept: 'application/json' }
    })
    return response.data.data   // because response has { success, message, data: {...} }
  } catch (error) {
    console.error('Failed to fetch analytics report:', error)
    throw new Error('Unable to load analytics report')
  }
}

// ─── Admin Analytics ───────────────────────────────────────────────

export interface AdminAnalyticsStats {
  total_webinars: number
  total_appointments: number
  revenue: number
  active_patients: number
  currency: string
}

export interface RevenueGraphPoint {
  year: number
  month: number
  month_label: string
  primary_revenue: number
  secondary_revenue: number
}

export interface AppointmentGraphPoint {
  year: number
  month: number
  month_label: string
  total_appointments: number
  amount_collected: number
}

export interface WebinarGraphPoint {
  year: number
  month: number
  month_label: string
  total_webinars: number
  amount_collected: number
}

export const fetchAdminAnalyticsStats = async (): Promise<AdminAnalyticsStats> => {
  try {
    const response = await api.get(`/v1/admin/analytics/stats`)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch admin analytics stats:', error)
    throw new Error('Unable to load admin analytics stats')
  }
}

export const fetchAdminRevenueGraph = async (): Promise<RevenueGraphPoint[]> => {
  try {
    const response = await api.get(`/v1/admin/analytics/graph`)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch revenue graph:', error)
    throw new Error('Unable to load revenue graph data')
  }
}

export const fetchAdminAppointmentsGraph = async (): Promise<AppointmentGraphPoint[]> => {
  try {
    const response = await api.get(`/v1/admin/analytics/graph/appointments`)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch appointments graph:', error)
    throw new Error('Unable to load appointments graph data')
  }
}

export const fetchAdminWebinarsGraph = async (): Promise<WebinarGraphPoint[]> => {
  try {
    const response = await api.get(`/v1/admin/analytics/graph/webinars`)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch webinars graph:', error)
    throw new Error('Unable to load webinars graph data')
  }
}