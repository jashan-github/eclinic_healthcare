import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import NotificationsPage from '@/pages/app/notifications'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/notifications')(
  {
    head: () => ({
      meta: [
        {
          title: getMetaTitle('Notifications')
        }
      ]
    }),
    loader: () => {
      useHeaderStore.getState().setPageTitle('Notifications')
    },
    component: RouteComponent
})

function RouteComponent() {

  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const role = (user?.role || roleFromStorage || '')
  
  return (
    <div className="overflow-auto">
      {role === 'patient' || role === 'doctor' ? (
        <NotificationsPage />
      ) : (
        <NotFound />
      )}
    </div>
  )
}
