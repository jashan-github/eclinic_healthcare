import { useQuery } from '@tanstack/react-query'
import {
  getPatientDashboard,
  type PatientDashboardResponse
} from '@/services/patient-dashboard-service'

// Hook to fetch patient dashboard data
export const usePatientDashboard = () => {
  return useQuery<PatientDashboardResponse, Error>({
    queryKey: ['patient-dashboard'],
    queryFn: getPatientDashboard,
    staleTime: 1000 * 60 * 2, // 2 minutes
    retry: 1,
    refetchOnWindowFocus: true
  })
}

