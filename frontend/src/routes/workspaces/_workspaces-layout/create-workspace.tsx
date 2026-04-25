import CreateWorkspace from '@/pages/workspaces/create-workspace'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/workspaces/_workspaces-layout/create-workspace')({
  component: CreateWorkspace,
  head: () => ({
    meta: [
      {
        title: 'Create Workspace'
      }
    ]
  })
})
