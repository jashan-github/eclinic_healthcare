import { getMedicalPracticeAreas } from '@/services/medical-practice-areas-service'
import type { MedicalPracticeArea } from '@/types/medical-practice-area'
import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'

/* 
   NOTE: [16-09-25] THIS IS A QUERY HOOK TO FETCH ALL THE PRACTICE AREAS,
   WHICH CAN BE MAPPED TO A DOCTOR. FOR FETCHING MAPPED PRACTICE AREAS, 
   USE usePracticeAreas HOOK
*/

// NOTE: THIS IS A QUERY HOOK TO FETCH ALL THE PRACTICE AREAS WHICH CAN BE MAPPED TO A DOCTOR.
export const useMedicalPracticeAreas = (searchQuery: string = '') => {
  // Debounce the search query
  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(searchQuery)
    }, 100) // 300ms debounce delay

    return () => {
      clearTimeout(handler)
    }
  }, [searchQuery])

  // Fetch Medical practice areas with query param
  const { data, isLoading, error } = useQuery<MedicalPracticeArea[], Error>({
    queryKey: ['medicalPracticeAreas', debouncedQuery],
    queryFn: () => getMedicalPracticeAreas({ q: debouncedQuery }),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: debouncedQuery.length === 0 || debouncedQuery.length >= 2 // Only fetch if query is empty or >= 2 chars
  })

  return {
    medicalPracticeAreas: data || [],
    isLoading,
    error
  }
}
