import PatientMedicalCertificates from '@/pages/app/patient/$patientId/medical-certificates'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/medical-certificates/'
)({
  component: PatientMedicalCertificates
})
