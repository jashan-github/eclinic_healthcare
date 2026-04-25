import SpecialitySettingsPage from '@/pages/app/settings/speciality-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/speciality-settings'
)({
  component: SpecialitySettingsPage
})
