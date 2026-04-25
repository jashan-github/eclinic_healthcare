import { useQuery } from '@tanstack/react-query'
import { getPatientPersonalInfo } from '@/services/patient-personal-info-service'

export const usePatientPersonalInfo = (enabled: boolean = true) => {
  return useQuery({
    queryKey: ['patientPersonalInfo'],
    queryFn: getPatientPersonalInfo,
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2
  })
}

