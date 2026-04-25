import { fetchMedicalHistoryOptions } from '@/services/medical-history-service'
import { useQuery } from '@tanstack/react-query'

export const useMedicalHistory = ({
  filterType,
  debouncedSearchTerm
}: {
  filterType: string
  debouncedSearchTerm: string
}) => {
  const { data, isFetching, isError, error } = useQuery({
    // The queryKey changes only when filterType or the *debounced* term changes,
    // which triggers the fetch.
    queryKey: ['medicalHistoryOptions', filterType, debouncedSearchTerm],

    // The queryFn is only called when enabled is true.
    queryFn: async () => {
      // The `fetchMedicalHistoryOptions` utility you provided
      const apiData = await fetchMedicalHistoryOptions(
        filterType,
        debouncedSearchTerm
      )

      return apiData
    },
    // Only enable the query if the debounced term is not empty and has a minimum length (e.g., 2 chars)
    enabled: debouncedSearchTerm.trim().length > 1
  })

  return {
    medicalHistoryOptions: data || [],
    isError,
    isFetching,
    error
  }
}
