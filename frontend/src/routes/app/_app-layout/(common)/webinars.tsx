import { useAuth } from '@/context/auth/auth-context-utils'
import { getMetaTitle } from '@/lib/utils'
import AdminWebinar from '@/pages/app/webinar/admin-webinar'
import DoctorWebinar from '@/pages/app/webinar/doctor-webinar'
import PatientWebinarsPage from '@/pages/app/patient/webinars'
import NotFound from '@/pages/not-found'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'
import type { UserRoleType } from '@/utils/user-role'

export const Route = createFileRoute('/app/_app-layout/(common)/webinars')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Webinars')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Webinars')
  },
  component: RouteComponent
})

function RouteComponent() {
  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const userRole = (user?.role || roleFromStorage || 'doctor') as UserRoleType
  const isPatient = userRole === 'patient'

  // For patients, show patient webinars UI
  if (isPatient) {
    return <PatientWebinarsPage />
  }

  // For doctors, show doctor webinars UI
  if (userRole === 'doctor') {
    return <DoctorWebinar />
  }

  // For admins, show admin webinars UI
  if (userRole === 'admin' || userRole === 'super_admin') {
    return <AdminWebinar />
  }

  return <NotFound />
}
