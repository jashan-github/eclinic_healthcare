import { getFirstAllowedRoute } from '@/utils/permission-utils'
import { createFileRoute, redirect } from '@tanstack/react-router'
import { lazy } from 'react'

const EClinicAuthLayout = lazy(() => import('@/layouts/auth-layout'))

export const Route = createFileRoute('/auth/_auth-layout')({
  beforeLoad: async ({ context }) => {
    if(!context.auth){
      return
    }
    if (context.auth.isAuthenticated && context.auth.user) {
      const { user, permissions } = context.auth
      const firstRoute = getFirstAllowedRoute(user.role, permissions ?? [])
      return redirect({ to: firstRoute })
    }
  },
  component: EClinicAuthLayout
})
