import GlobalLoader from '@/components/orvo/common/global-loader'
import NewPatientPage from '@/pages/app/patient/new'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/new'
)({
  component: NewPatientPage,
  head: () => ({
    meta: [
      {
        title: 'New Patient '
      }
    ]
  }),
  pendingComponent: GlobalLoader
})
