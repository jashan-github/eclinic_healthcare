import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import DoctorsPage from '@/pages/app/doctors'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/doctors')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Doctors')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Doctors')
  },
  component: RouteComponent
})

function RouteComponent() {
  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const role = (user?.role || roleFromStorage || '')

  if (role !== 'patient') {
    return <NotFound />
  }
  return (
    <div className="h-full overflow-y-auto bg-[#F4F6F9]">
      <DoctorsPage />
    </div>
  )
}

