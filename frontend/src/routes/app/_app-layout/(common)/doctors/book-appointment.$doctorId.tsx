import { getMetaTitle } from '@/lib/utils'
import BookAppointmentPage from '@/pages/app/patient/appointments/book-appointment'
import { useHeaderStore } from '@/store/use-header-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app/_app-layout/(common)/doctors/book-appointment/$doctorId')({
  head: () => ({
    meta: [
      {
        title: getMetaTitle('Book Appointment')
      }
    ]
  }),
  loader: () => {
    useHeaderStore.getState().setPageTitle('Book Appointment')
  },
  component: RouteComponent
})

function RouteComponent() {
  return (
    <div className="h-full overflow-y-auto">
      <BookAppointmentPage />
    </div>
  )
}
