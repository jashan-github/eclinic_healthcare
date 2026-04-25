import ContactPage from '@/pages/public/contact'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/(public)/_public_layout/contact')({
  component: ContactPage,
  head: () => ({
    meta: [
      {
        title: 'Contact Us - Salutogena'
      }
    ]
  })
})
