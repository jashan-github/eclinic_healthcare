import { getAllLanguages } from '@/services/language-service'
import { useQuery } from '@tanstack/react-query'

export const useLanguages = () => {
  const {
    data: languages,
    isLoading,
    error
  } = useQuery({
    queryKey: ['globalLanguages'],
    queryFn: getAllLanguages,
    staleTime: 1000 * 60 * 5
  })

  return {
    languages: languages || [],
    isLoading,
    error
  }
}
