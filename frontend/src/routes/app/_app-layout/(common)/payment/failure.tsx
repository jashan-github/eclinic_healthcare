import { createFileRoute } from '@tanstack/react-router'
import PaymentFailurePage from '@/pages/app/payment/failure'

export const Route = createFileRoute('/app/_app-layout/(common)/payment/failure')({
  component: PaymentFailurePage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      payment_id: (search.payment_id as string) || undefined,
      reason: (search.reason as string) || undefined,
    }
  },
})

