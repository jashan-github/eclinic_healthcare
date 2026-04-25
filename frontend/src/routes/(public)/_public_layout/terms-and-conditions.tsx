import TermsAndConditionsPage from '@/pages/public/terms-and-conditions'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/(public)/_public_layout/terms-and-conditions'
)({
  component: TermsAndConditionsPage,
  head: () => ({
    meta: [
      {
        title: 'Terms & Conditions - Salutogena'
      }
    ]
  })
})
