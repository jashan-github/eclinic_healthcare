import { fetchAllAssociatedClinics } from '@/services/clinics-service'
import { useQuery } from '@tanstack/react-query'

export const useAssociatedClinics = () => {
  // Get all Clinics associated with the authenticated doctor
  const { data, isLoading, error } = useQuery({
    queryKey: ['associatedClinics'],
    queryFn: fetchAllAssociatedClinics,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    associatedClinics: data || [],
    associatedClinicsFormatted: data
      ? data.map((service) => ({
          value: service.id,
          label: service.name
        }))
      : [],
    isLoading,
    error
  }
}
