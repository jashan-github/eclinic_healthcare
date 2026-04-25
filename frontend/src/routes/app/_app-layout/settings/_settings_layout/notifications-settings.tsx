import AdminNotificationsSettingsPage from '@/pages/app/settings/admin-notifications-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/notifications-settings'
)({
  component: AdminNotificationsSettingsPage
})

