import StaffRestrictions from '@/pages/app/settings/staff-restrictions'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/staff-restrictions'
)({
  component: RouteComponent
})

function RouteComponent() {
  return (
   <StaffRestrictions />
  )
}
