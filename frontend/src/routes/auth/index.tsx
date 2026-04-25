import NotFound from '@/pages/not-found'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/auth/')({
  component: NotFound
})
