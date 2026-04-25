import { getAllMedicalCouncils } from '@/services/medical-councils-service'
import type { MedicalCouncil } from '@/types/medical-council'
import { useQuery } from '@tanstack/react-query'

export const useMedicalCouncils = () => {
  // Get all medical registration councils.
  const { data, isLoading, error } = useQuery<MedicalCouncil[], Error>({
    queryKey: ['medicalCouncils'],
    queryFn: getAllMedicalCouncils,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    medicalCouncils: data || [],
    isLoadingMedicalCouncils: isLoading,
    error
  }
}
