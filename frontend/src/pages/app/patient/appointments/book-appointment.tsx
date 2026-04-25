import { useNavigate, useParams } from '@tanstack/react-router'
import BookAppointmentForm from '@/components/e-clinic/patient/doctors/book-appointment/book-appointment-form'

const BookAppointmentPage = () => {
  const navigate = useNavigate()
  const { doctorId } = useParams({ from: '/app/_app-layout/(common)/doctors/book-appointment/$doctorId' })

  const handleBack = () => {
    navigate({ to: '/app/doctors' })
  }

  return (
    <div className="h-full overflow-y-auto bg-[#F4F6F9]">
      <BookAppointmentForm
        doctorId={doctorId}
        onBack={handleBack}
      />
    </div>
  )
}

export default BookAppointmentPage

