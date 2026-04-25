import { createFileRoute, redirect } from '@tanstack/react-router'

// Redirect /app/settings to the settings layout default tab.
// Admins land on their settings; others land on staff restrictions.
export const Route = createFileRoute('/app/_app-layout/settings/')({
  beforeLoad: ({ context }) => {
    const role = context.auth.user?.role || localStorage.getItem('role') || 'doctor'
    const isAdmin =
      role === 'admin' || role === 'super_admin' || role === 'clinic_admin'

    const redirectTo = isAdmin
      ? '/app/settings/general-settings'
      : '/app/settings/staff-restrictions'

    throw redirect({ to: redirectTo })
  }
})
