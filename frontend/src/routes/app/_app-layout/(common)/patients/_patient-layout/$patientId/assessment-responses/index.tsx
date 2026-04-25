import AssessmentResponses from '@/pages/app/patient/$patientId/assessment-responses'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/assessment-responses/'
)({
  component: AssessmentResponses
})
