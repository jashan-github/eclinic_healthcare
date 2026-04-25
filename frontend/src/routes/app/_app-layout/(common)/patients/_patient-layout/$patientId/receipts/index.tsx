import PatientReceiptsPage from '@/pages/app/patient/$patientId/receipts'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/receipts/'
)({
  component: PatientReceiptsPage
})
