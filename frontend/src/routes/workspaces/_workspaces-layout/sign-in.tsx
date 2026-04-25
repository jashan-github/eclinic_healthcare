import SignIn from '@/pages/workspaces/sign-in'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/workspaces/_workspaces-layout/sign-in')({
  component: SignIn,
  head: () => ({
    meta: [
      {
        title: 'Workspaces'
      }
    ]
  })
})
