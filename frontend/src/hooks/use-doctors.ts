import { useQuery } from '@tanstack/react-query'
import { searchDoctors, type DoctorSearchFilters } from '@/services/doctors-service'

export const useDoctors = (filters?: DoctorSearchFilters) => {
  return useQuery({
    queryKey: ['doctors', filters],
    queryFn: () => searchDoctors(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    enabled: true
  })
}

