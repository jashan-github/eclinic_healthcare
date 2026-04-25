import PublicLayout from '@/layouts/public-layout'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/(public)/_public_layout')(
  {
    component: PublicLayout
  }
)
