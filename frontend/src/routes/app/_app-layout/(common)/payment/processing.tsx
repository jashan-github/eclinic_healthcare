import { createFileRoute } from '@tanstack/react-router'
import PaymentProcessingPage from '@/pages/app/payment/processing'

export const Route = createFileRoute('/app/_app-layout/(common)/payment/processing')({
  component: PaymentProcessingPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      payment_id: (search.payment_id as string) || undefined,
      status: (search.status as string) || undefined,
    }
  },
})

