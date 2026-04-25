// src/services/forgot-password.ts
import api from '@/lib/api'

export interface ForgotPasswordResponse {
  success: boolean
  message: string
  data?: any
  errors?: any
}

export const sendPasswordReset = async (email: string): Promise<ForgotPasswordResponse> => {
  try {
    const response = await api.post<ForgotPasswordResponse>(`/v1/emails/reset-password`, { email })
    return response.data
  } catch (error: any) {
    console.error('Failed to send password reset:', error)
    throw new Error(error.response?.data?.message || 'Unable to send password reset request')
  }
}