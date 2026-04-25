import AdminLoginForm from '@/features/auth/components/admin-login-form'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/auth/_auth-layout/admin-login')({
  component: AdminLoginForm,
})
