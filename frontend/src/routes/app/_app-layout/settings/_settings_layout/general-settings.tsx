import AdminGeneralSettingsPage from '@/pages/app/settings/admin-general-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/general-settings'
)({
  component: AdminGeneralSettingsPage
})

