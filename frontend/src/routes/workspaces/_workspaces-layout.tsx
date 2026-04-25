import WorkspaceLayout from '@/layouts/workspace-layout'
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/workspaces/_workspaces-layout')({
  beforeLoad: async ({ context }) => {
    if (context.auth.isAuthenticated) {
      return redirect({ to: '/setup/sign-in' })
    }
  },
  component: WorkspaceLayout
})
