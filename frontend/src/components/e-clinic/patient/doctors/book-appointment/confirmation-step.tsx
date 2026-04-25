import { CheckCircleIcon } from '@phosphor-icons/react'
import { useNavigate } from '@tanstack/react-router'

interface ConfirmationStepProps {
  doctorName: string
  consultationType: 'teleconsultation' | 'in-clinic' | null
  selectedDate: string
  selectedTime: string
  symptoms: string
}

const ConfirmationStep = ({
  doctorName,
  consultationType,
  selectedDate,
  selectedTime,
  symptoms
}: ConfirmationStepProps) => {
  const navigate = useNavigate()

  const handleGoToAppointments = () => {
    navigate({ to: '/app/appointments' })
  }

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
      <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#002FD4] mb-6">
        Confirmation
      </h2>
      
      <div className="flex flex-col items-center text-center py-8">
        <CheckCircleIcon size={80} weight="fill" className="text-green-500 mb-6" />
        <h2 className="font-poppins font-bold text-[28px] leading-[36px] text-[#0F1011] mb-2">
          Appointment Scheduled!
        </h2>
        <p className="font-poppins font-normal text-[16px] leading-[24px] text-[#64748B] mb-8">
          Your appointment is scheduled with {doctorName}
        </p>

        {/* Appointment Details Card */}
        <div className="w-full bg-[#F4F6F9] rounded-lg p-6 mb-6">
          <h3 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-4 text-left">
            Appointment Details:
          </h3>
          <div className="space-y-3 text-left">
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Healthcare Provider:
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {doctorName}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Type:
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {consultationType === 'teleconsultation' ? 'Online Consultation' : 'In-Clinic'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Date:
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {selectedDate}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Time:
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {selectedTime}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#545D69]">
                Symptoms:
              </span>
              <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
                {symptoms}
              </span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleGoToAppointments}
          className="w-full bg-[#002FD4] hover:bg-[#001FB8] text-white font-poppins font-semibold 
            text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors"
        >
          Go to Appointments
        </button>
      </div>
    </div>
  )
}

export default ConfirmationStep

