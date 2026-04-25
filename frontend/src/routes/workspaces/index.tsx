import NotFound from '@/pages/not-found'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/workspaces/')({
  component: NotFound
})
