import { useAuth } from '@/context/auth/auth-context-utils'
import BillingContent from '@/pages/app/staff/billing'
import NotFound from '@/pages/not-found'
import type { UserRoleType } from '@/utils/user-role'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(staff)/billing')({
  component: RouteComponent,
})

function RouteComponent() {
  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const userRole = (user?.role || roleFromStorage || 'Doctor') as UserRoleType
  const isStaff = userRole === 'staff'

  if (isStaff) {
    return <BillingContent />
  }
  
  return <NotFound />
}