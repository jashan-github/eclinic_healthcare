import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute(
  '/app/_app-layout/(common)/patients/_patient-layout/$patientId/visits/$visitId'
)({
  component: RouteComponent
})

function RouteComponent() {
  return (
    <div>
      Hello
      "/app/_app-layout/patient/_patient-layout/$patientId/visits/$visitId"!
    </div>
  )
}
