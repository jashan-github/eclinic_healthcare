import FeesSettings from '@/pages/app/settings/fees-settings'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/fees-settings'
)({
  component: RouteComponent
})

function RouteComponent() {
  return (
      <FeesSettings />
  )
}
