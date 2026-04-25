import { createFileRoute } from '@tanstack/react-router'
import PaymentSuccessPage from '@/pages/app/payment/success'

export const Route = createFileRoute('/app/_app-layout/(common)/payment/success')({
  component: PaymentSuccessPage,
  validateSearch: (search: Record<string, unknown>) => {
    return {
      payment_id: (search.payment_id as string) || undefined,
      status: (search.status as string) || undefined,
    }
  },
})

