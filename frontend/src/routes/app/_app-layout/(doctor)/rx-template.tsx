import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import RxTemplate from '@/pages/app/rx-template'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(doctor)/rx-template')({
  component: function RxTemplateRoute() {
    const { user } = useAuth()
    const roleFromStorage = localStorage.getItem('role')
    const role = (user?.role || roleFromStorage || '')

    if (role !== 'doctor') {
      return <NotFound />
    }

    return <RxTemplate />
  },
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Rx Template')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Rx Template')
  }
})
