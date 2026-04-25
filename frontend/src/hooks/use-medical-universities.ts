import { getAllMedicalUniversities } from '@/services/medical-universities-service'
import type { MedicalUniversity } from '@/types/medical-university'
import { useQuery } from '@tanstack/react-query'

export const useMedicalUniversities = () => {
  // Get list of all medical universities.
  const { data, isLoading, error } = useQuery<MedicalUniversity[], Error>({
    queryKey: ['medicalUniversities'],
    queryFn: getAllMedicalUniversities,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    medicalUniversities: data || [],
    isLoading,
    error
  }
}
