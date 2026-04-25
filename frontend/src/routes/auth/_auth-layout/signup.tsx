import Signup from '@/pages/auth/signup'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/auth/_auth-layout/signup')({
  component: Signup
})

