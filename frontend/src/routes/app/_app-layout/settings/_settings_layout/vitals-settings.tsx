import VitalsSettings from '@/pages/app/settings/vitals-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/vitals-settings'
)({
  component: VitalsSettings
})

