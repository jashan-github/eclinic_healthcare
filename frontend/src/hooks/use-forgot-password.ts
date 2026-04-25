// src/hooks/use-forgot-password.ts
import { sendPasswordReset, type ForgotPasswordResponse } from '@/services/forgot-password'
import { useMutation } from '@tanstack/react-query'

export const useForgotPassword = () => {
  return useMutation<ForgotPasswordResponse, Error, string>({
    mutationFn: sendPasswordReset,
    mutationKey: ['forgot-password'],
  })
}