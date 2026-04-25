import PrivacyPolicyPage from '@/pages/public/privacy-policy'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/(public)/_public_layout/privacy-policy')(
  {
    component: PrivacyPolicyPage,
    head: () => ({
      meta: [
        {
          title: 'Contact Us - Privacy Policy'
        }
      ]
    })
  }
)
