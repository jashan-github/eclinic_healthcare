import { useAuth } from '@/context/auth/auth-context-utils'
import PatientData from '@/pages/app/staff/patient-data'
import NotFound from '@/pages/not-found'
import type { UserRoleType } from '@/utils/user-role'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(staff)/patient-data')({
  component: RouteComponent,
})

function RouteComponent() {
  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const userRole = (user?.role || roleFromStorage || 'doctor') as UserRoleType
  const isStaff = userRole === 'staff'

  if (isStaff) {
    return <PatientData />
  }
  
  return <NotFound />
}