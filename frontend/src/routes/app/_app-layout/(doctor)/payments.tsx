import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import PaymentsPage from '@/pages/app/payments'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(doctor)/payments')({
  component: function DoctorPaymentsRoute() {
    const { user } = useAuth()
    const roleFromStorage = localStorage.getItem('role')
    const role = (user?.role || roleFromStorage || '')

    if (role !== 'doctor') {
      return <NotFound />
    }

    return <PaymentsPage />
  },
  loader: () => {
    useHeaderStore.getState().setPageTitle('Payments')
  },
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Payments')
      }
    ]
  })
})
