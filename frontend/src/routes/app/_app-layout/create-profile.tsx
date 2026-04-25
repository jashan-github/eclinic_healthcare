import CreateProfile from '@/pages/app/create-profile'
import { getFirstAllowedRoute } from '@/utils/permission-utils'
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/create-profile')({
  beforeLoad: async ({ context }) => {
    // If profile is already completed, redirect based on role
    if (context.auth.user?.is_profile_complete) {
      const user = context.auth.user
      const roleFromStorage = localStorage.getItem('role')
      const userRole = user?.role || roleFromStorage || 'doctor'
      const permissions = context.auth.permissions ?? []

      const redirectTo = getFirstAllowedRoute(userRole, permissions)
      throw redirect({ to: redirectTo })
    }
  },
  component: CreateProfile,
})