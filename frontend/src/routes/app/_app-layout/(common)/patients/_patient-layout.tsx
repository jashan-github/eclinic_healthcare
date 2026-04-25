import PatientDetailsLayout from '@/layouts/patient-details-layout'
import { getMetaTitle } from '@/lib/utils'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout'
)({
  component: PatientDetailsLayout,
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Patients')
      }
    ]
  })
})
