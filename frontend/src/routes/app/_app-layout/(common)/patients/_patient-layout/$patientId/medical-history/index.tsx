import MedicalHistory from '@/pages/app/patient/$patientId/medical-history'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/medical-history/'
)({
  component: MedicalHistory
})
