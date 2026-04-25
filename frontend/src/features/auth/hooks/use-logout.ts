import { useMutation } from '@tanstack/react-query'
import { logoutUser } from '../services/authentication-service'
import { tokenCookies } from '@/utils/cookies'

export const useLogout = () => {
  return useMutation<
    { success: boolean; message: string },
    Error,
    void
  >({
    mutationFn: async () => {
      const response = await logoutUser()
      
      // Clear tokens from cookies after successful logout
      tokenCookies.removeAllTokens()
      localStorage.removeItem('role')
      return response
    },
    onError: (error) => {
      console.error('[useLogout] Error:', error)
      // Even if API call fails, clear tokens locally
      tokenCookies.removeAllTokens()
      localStorage.removeItem('role')
    },
  })
}
