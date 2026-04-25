import PatientDetailsPage from '@/pages/app/patient/$patientId'
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/'
)({
  beforeLoad: () => {
    throw redirect({ to: 'visits' })
  },
  component: PatientDetailsPage
})
