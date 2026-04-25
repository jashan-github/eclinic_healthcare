import { getAllSpecializations } from '@/features/app/my-profile/services/specializations-services'
import { useQuery } from '@tanstack/react-query'

export const useLanguages = () => {
  const {
    data: languages,
    isLoading,
    error
  } = useQuery({
    queryKey: ['globalLanguages'],
    queryFn: getAllSpecializations,
    staleTime: 1000 * 60 * 5
  })

  return {
    languages: languages || [],
    isLoading,
    error
  }
}
