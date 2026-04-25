import AdminWaiverSettingsPage from '@/pages/app/settings/admin-waiver-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/waiver-referral-settings'
)({
  component: AdminWaiverSettingsPage
})

