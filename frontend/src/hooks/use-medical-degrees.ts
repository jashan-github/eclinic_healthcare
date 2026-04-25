import { getAllMedicalDegrees } from '@/services/medical-degrees-service'
import type { MedicalDegree } from '@/types/medical-degree'
import { useQuery } from '@tanstack/react-query'

export const useMedicalDegrees = () => {
  // Get list of all medical degrees.
  const { data, isLoading, error } = useQuery<MedicalDegree[], Error>({
    queryKey: ['medicalDegrees'],
    queryFn: getAllMedicalDegrees,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    medicalDegrees: data || [],
    isLoading,
    error
  }
}
