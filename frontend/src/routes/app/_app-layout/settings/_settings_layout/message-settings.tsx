import ComingSoonPage from '@/components/orvo/common/coming-soon-page'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/settings/_settings_layout/message-settings'
)({
  component: RouteComponent
})

function RouteComponent() {
  return (
    <div className="h-screen overflow-hidden flex flex-col w-full justify-center items-center">
      <ComingSoonPage />
    </div>
  )
}
