import { getMetaTitle } from '@/lib/utils'
import AdminDashboard from '@/pages/app/dashboard/dashboard-admin'
import PatientDashboard from '@/pages/app/patient/dashboard'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '@/context/auth/auth-context-utils'
import NotFound from '@/pages/not-found'
import StaffDashboard from '@/pages/app/staff/dashboard'
// import type { UserRoleType } from '@/utils/user-role'

export const Route = createFileRoute('/app/_app-layout/(common)/dashboard')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Dashboard')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Dashboard')
  },
  component: RouteComponent
})

function RouteComponent() {

  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const role = (user?.role || roleFromStorage || '')
  const isAdmin = role === 'admin' || role === 'super_admin' || role === 'clinic_admin'
  return (
    <div className="overflow-auto">
      {role === 'patient' ? (
        <PatientDashboard />
      ) : isAdmin ? (
        <AdminDashboard />
      ) : role === 'staff' ? (
        <StaffDashboard />
      ) : (
        <NotFound />
      )}
    </div>
  )
}
