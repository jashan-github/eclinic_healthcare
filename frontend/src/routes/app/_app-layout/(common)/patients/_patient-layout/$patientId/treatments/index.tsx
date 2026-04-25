import PatientTreatments from '@/pages/app/patient/$patientId/treatments'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/treatments/'
)({
  component: PatientTreatments
})
