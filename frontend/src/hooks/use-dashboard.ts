import {
  fetchDashboardStats,
  fetchDashboardRevenueGraph,
  fetchDashboardRecentActivity,
  fetchDashboardActiveAppointments,
  type DashboardStats,
  type DashboardRevenuePoint,
  type RecentActivityItem,
  type ActiveAppointmentsResponse,
} from '@/services/dashboard'
import { useQuery } from '@tanstack/react-query'

export const useDashboardStats = () => {
  return useQuery<DashboardStats, Error>({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useDashboardRevenueGraph = (months = 6) => {
  return useQuery<DashboardRevenuePoint[], Error>({
    queryKey: ['dashboard-revenue-graph', months],
    queryFn: () => fetchDashboardRevenueGraph(months),
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useDashboardRecentActivity = (limit = 20, status = 'all') => {
  return useQuery<RecentActivityItem[], Error>({
    queryKey: ['dashboard-recent-activity', limit, status],
    queryFn: () => fetchDashboardRecentActivity(limit, status),
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useDashboardActiveAppointments = (limit = 20, status = 'all') => {
  return useQuery<ActiveAppointmentsResponse, Error>({
    queryKey: ['dashboard-active-appointments', limit, status],
    queryFn: () => fetchDashboardActiveAppointments(limit, status),
    staleTime: 1 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}
