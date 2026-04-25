import ResetPasswordPage from '@/features/auth/components/reset-password'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/auth/_auth-layout/reset-password')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <ResetPasswordPage />
  )
}
