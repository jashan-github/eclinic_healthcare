import PatientOverview from '@/pages/app/patient/$patientId/patient-overview'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/patient-overview/'
)({
  component: PatientOverview
})
