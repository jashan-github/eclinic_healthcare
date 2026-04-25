// src/hooks/use-reset-password.ts
import { resetPassword, type ResetPasswordResponse } from '@/services/reset-password'
import { useMutation } from '@tanstack/react-query'

export const useResetPassword = () => {
  return useMutation<ResetPasswordResponse, Error, { email: string; token: string; password: string; confirm_password: string }>({
    mutationFn: ({ email, token, password, confirm_password }) => resetPassword(email, token, password, confirm_password),
    mutationKey: ['reset-password'],
  })
}