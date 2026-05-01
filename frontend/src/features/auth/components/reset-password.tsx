import { Button, Text, PasswordInput } from '@mantine/core'
import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { type FC } from 'react'
import { useResetPassword } from '@/hooks/user-reset-password'

const resetPasswordSchema = z
  .object({
    password: z.string().min(8, { message: 'Password must be at least 8 characters long' }),
    confirmPassword: z.string().min(8, { message: 'Confirm password must be at least 8 characters long' })
  })
  .refine(
    (data) => data.password === data.confirmPassword,
    {
      message: 'Passwords do not match',
      path: ['confirmPassword']
    }
  )

const ResetPasswordPage: FC = () => {
  const { token, email } = useSearch({ strict: false }) as { token?: string; email?: string }
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const navigate = useNavigate()

  // Use the mutation hook
  const mutation = useResetPassword()

  // Check if token or email is missing and redirect to verification failed page
  useEffect(() => {
    if (!token || !email) {
      navigate({ to: '/auth/reset-password-verification-failed' })
    }
  }, [token, email, navigate])

  // Don't render form if token or email is missing
  if (!token || !email) {
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const payload = { password, confirmPassword }
    const result = resetPasswordSchema.safeParse(payload)

    if (!result.success) {
      result.error.issues.forEach((issue) => toast.error(issue.message))
      return
    }

    mutation.mutate({ email, token, password: result.data.password, confirm_password: confirmPassword }, {
      onSuccess: (data) => {
        toast.success(data.message || 'Password reset successfully!')

        // Redirect to login
        navigate({ to: '/auth/login' })
      },
      onError: (error: any) => {
        // Only redirect to verification-failed when the error is actually about the
        // token/link itself. 400 responses are typically validation errors (e.g. weak
        // password) and must not trigger the verification-failed flow.
        const errorMessage = error.message || error.response?.data?.message || ''
        const isVerificationError =
          errorMessage.toLowerCase().includes('invalid') ||
          errorMessage.toLowerCase().includes('expired') ||
          errorMessage.toLowerCase().includes('token') ||
          errorMessage.toLowerCase().includes('verification') ||
          error.response?.status === 401 ||
          error.response?.status === 403

        if (isVerificationError) {
          navigate({ to: '/auth/reset-password-verification-failed' })
        } else {
          toast.error(errorMessage || 'Failed to reset password. Please try again.')
        }
      },
    })
  }

  // Loading state from mutation
  const isLoading = mutation.isPending

  return (
    <div className="mx-auto flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-[6px_7px_20px_0px_rgba(0,0,0,0.10)] py-6 px-5 sm:px-6">

          <div className="flex justify-center mb-8">
            <img src="/assets/icons/e-clinic-logo-full.svg" alt="E-Clinic" className="w-[120px] h-auto sm:w-[150px]" />
          </div>

          <div className="text-center mb-8">
            <h1 className="font-poppins font-bold text-2xl text-[#0F1011] mb-2">Set New Password</h1>
            <p className="font-poppins text-sm text-gray-600">
              Choose a strong password for your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Text size="sm" fw={400} mb={6} className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]">
                New Password
              </Text>
              <PasswordInput
                placeholder="Enter new password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                size="md"
                required
                styles={{ input: { fontSize: '14px', border: '1px solid #E2E8F0', borderRadius: '8px', height: '44px' } }}
                classNames={{ input: 'font-poppins border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:text-[#64748B] focus:border-[#002FD4]' }}
              />
            </div>

            <div>
              <Text size="sm" fw={400} mb={6} className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]">
                Confirm Password
              </Text>
              <PasswordInput
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                size="md"
                required
                styles={{ input: { fontSize: '14px', border: '1px solid #E2E8F0', borderRadius: '8px', height: '44px' } }}
                classNames={{ input: 'font-poppins border-[#E2E8F0] rounded-[8px] placeholder:font-poppins placeholder:text-[14px] placeholder:text-[#64748B] focus:border-[#002FD4]' }}
              />
            </div>

            <Button
              type="submit"
              fullWidth
              loading={isLoading}
              disabled={isLoading}
              size="md"
              className="bg-[#002FD4] h-11 rounded-md font-poppins font-semibold text-sm text-[#F8FAFC] hover:bg-[#0020B0]"
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </Button>
          </form>

          <div className="text-center mt-6">
            <Link to="/auth/login" className="text-sm text-[#002FD4] font-poppins font-medium hover:underline">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResetPasswordPage