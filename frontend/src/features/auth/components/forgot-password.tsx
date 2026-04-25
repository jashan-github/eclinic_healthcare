import { Button, Text, TextInput } from '@mantine/core'
import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { type FC } from 'react'
import { useForgotPassword } from '@/hooks/use-forgot-password'

const forgotPasswordSchema = z
  .object({
    email: z.string().min(1, { message: 'This field is required' })
  })
  .refine(
    (data) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email),
    {
      message: 'Please enter a valid email address',
      path: ['email']
    }
  )

const ForgotPasswordPage: FC = () => {
  const [email, setEmail] = useState('')

  // Use the mutation hook
  const mutation = useForgotPassword()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const result = forgotPasswordSchema.safeParse({ email })

    if (!result.success) {
      result.error.issues.forEach((issue) => toast.error(issue.message))
      return
    }

    mutation.mutate(email, {
      onSuccess: () => {
        toast.success('Password reset link sent to your email! Check your inbox (and spam folder).')
      },
      onError: (error: any) => {
        toast.error(error.message || 'Failed to send reset link. Please try again.')
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
            <h1 className="font-poppins font-bold text-2xl text-[#0F1011] mb-2">Reset Password</h1>
            <p className="font-poppins text-sm text-gray-600">
              Enter your email and we’ll send you a link to reset your password
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Text size="sm" fw={400} mb={6} className="font-poppins font-semibold text-[14px] leading-[20px] tracking-[0] text-[#0F1011]">
                Email
              </Text>
              <TextInput
                type="email"
                inputMode="email"
                autoComplete="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
              {isLoading ? 'Sending Link...' : 'Send Reset Link'}
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

export default ForgotPasswordPage