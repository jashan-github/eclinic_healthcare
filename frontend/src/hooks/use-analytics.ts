// src/hooks/use-analytics-overview.ts
import {
  fetchAnalyticsOverview,
  fetchAnalyticsReport,
  fetchAnalyticsSummary,
  fetchAdminAnalyticsStats,
  fetchAdminRevenueGraph,
  fetchAdminAppointmentsGraph,
  fetchAdminWebinarsGraph,
  type AnalyticsOverview,
  type AnalyticsReport,
  type AdminAnalyticsStats,
  type RevenueGraphPoint,
  type AppointmentGraphPoint,
  type WebinarGraphPoint,
} from '@/services/analytics'
import { useQuery } from '@tanstack/react-query'

export const useAnalyticsOverview = () => {
  return useQuery<AnalyticsOverview, Error>({
    queryKey: ['analytics-overview'],
    queryFn: fetchAnalyticsOverview,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useAnalyticsSummary = () => {
  return useQuery({
    queryKey: ['analytics-summary'],
    queryFn: fetchAnalyticsSummary,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useAnalyticsReport = () => {
  return useQuery<AnalyticsReport, Error>({
    queryKey: ['analytics-report'],
    queryFn: fetchAnalyticsReport,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

// ─── Admin Analytics Hooks ─────────────────────────────────────────

export const useAdminAnalyticsStats = () => {
  return useQuery<AdminAnalyticsStats, Error>({
    queryKey: ['admin-analytics-stats'],
    queryFn: fetchAdminAnalyticsStats,
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useAdminRevenueGraph = () => {
  return useQuery<RevenueGraphPoint[], Error>({
    queryKey: ['admin-revenue-graph'],
    queryFn: fetchAdminRevenueGraph,
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useAdminAppointmentsGraph = () => {
  return useQuery<AppointmentGraphPoint[], Error>({
    queryKey: ['admin-appointments-graph'],
    queryFn: fetchAdminAppointmentsGraph,
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useAdminWebinarsGraph = () => {
  return useQuery<WebinarGraphPoint[], Error>({
    queryKey: ['admin-webinars-graph'],
    queryFn: fetchAdminWebinarsGraph,
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}