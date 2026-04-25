import { useMutation } from '@tanstack/react-query'
import { refreshToken, type RefreshTokenResponse, type NewApiResponse } from '../services/authentication-service'
import { tokenCookies } from '@/utils/cookies'

export const useRefreshToken = () => {
  return useMutation<
    NewApiResponse<RefreshTokenResponse>,
    Error,
    string
  >({
    mutationFn: async (refreshTokenValue: string) => {
      const response = await refreshToken(refreshTokenValue)
      
      // Store new tokens in cookies
      if (response.success && response.data) {
        tokenCookies.setAccessToken(response.data.access_token)
        tokenCookies.setRefreshToken(response.data.refresh_token)
      }
      
      return response
    },
    onError: (error) => {
      console.error('[useRefreshToken] Error:', error)
      // Clear tokens on error
      tokenCookies.removeAllTokens()
    },
  })
}
