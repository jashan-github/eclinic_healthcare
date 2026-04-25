import {
  fetchAllSocialLinks,
  saveAllSocialLinks
} from '@/features/app/my-profile/services/social-links-service'
import type { SocialLinks } from '@/types/social-links'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export const useSocialLinks = () => {
  const queryClient = useQueryClient()

  // Fetch social links
  const { data, isLoading, error } = useQuery<SocialLinks, Error>({
    queryKey: ['socialLinks'],
    queryFn: fetchAllSocialLinks,
    staleTime: 1000 * 60 * 60 // 5 minutes
  })

  // Save social links
  const mutation = useMutation({
    mutationFn: saveAllSocialLinks,
    onSuccess: () => {
      // Invalidate the social links query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['socialLinks'] })
    },
    onError: (error) => {
      console.error('Failed to save social links:', error)
    }
  })

  return {
    socialLinks: data || {
      facebook_link: '',
      linkedIn_link: '',
      instagram_link: '',
      twitter_link: '',
      youTube_link: ''
    },
    isLoading,
    error,
    saveSocialLinks: mutation.mutate,
    isSaving: mutation.isPending
  }
}
