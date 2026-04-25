import SentFilesPage from '@/pages/app/patient/$patientId/sent-files'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/sent-files/'
)({
  component: SentFilesPage
})
