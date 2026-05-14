import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import RequestsPage from '@/pages/app/doctor/requests'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(doctor)/requests')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Requests')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Requests')
  },
  component: function RequestsRoute() {
    const { user } = useAuth()
    const roleFromStorage = localStorage.getItem('role')
    const role = (user?.role || roleFromStorage || '')

    if (role !== 'doctor') {
      return <NotFound />
    }

    return <RequestsPage />
  },
})
