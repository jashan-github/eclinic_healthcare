import CreateProfile from '@/pages/workspaces/create-profile'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/workspaces/_workspaces-layout/create-profile'
)({
  component: CreateProfile,
  head: () => ({
    meta: [
      {
        title: 'Create Profile'
      }
    ]
  })
})
