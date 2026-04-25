// src/services/reset-password.ts
import api from '@/lib/api'

export interface ResetPasswordResponse {
  message: string
}

export const resetPassword = async (email: string, token: string, password: string, confirm_password: string): Promise<ResetPasswordResponse> => {
  try {
    // Build payload - email might be optional if token contains email info
    const payload: any = { token, password, confirm_password }
    if (email) {
      payload.email = email
    }
    
    const response = await api.post(`/v1/emails/reset-password-confirm`, payload)
    return response.data
  } catch (error: any) {
    console.error('Failed to reset password:', error)
    throw new Error(error.response?.data?.message || 'Unable to reset password')
  }
}
