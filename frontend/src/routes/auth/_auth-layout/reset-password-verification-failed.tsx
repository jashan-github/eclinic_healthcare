import ResetPasswordVerificationFailedPage from '@/features/auth/components/reset-password-verification-failed'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/auth/_auth-layout/reset-password-verification-failed')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <ResetPasswordVerificationFailedPage />
  )
}

