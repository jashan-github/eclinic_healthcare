import { CheckCircleIcon } from '@phosphor-icons/react'

interface AppointmentRequestSubmittedStepProps {
  doctorName: string
  status?: string
}

const AppointmentRequestSubmittedStep = ({
  doctorName,
  status = 'PENDING'
}: AppointmentRequestSubmittedStepProps) => {
  // Different messages based on appointment status
  const getTitle = () => {
    if (status === 'ACCEPTED') {
      return 'Appointment Confirmed!'
    }
    return 'Appointment Request Submitted!'
  }

  const getMessage = () => {
    if (status === 'ACCEPTED') {
      return `Great news! Your appointment with ${doctorName} has been confirmed. Please proceed to payment to complete your booking.`
    }
    return `Your appointment request has been sent to ${doctorName} for approval. You will receive a notification for the payment once the healthcare provider responds.`
  }

  return (
    <div className='bg-white w-full h-full flex items-center justify-center p-6'>
      <div className="bg-[#E8F0FE] rounded-lg border border-[#E4E5ED] p-8 w-full max-w-2xl">
        <div className="flex flex-col items-center text-center py-8">
          <CheckCircleIcon 
            size={80} 
            weight="fill" 
            className={status === 'ACCEPTED' ? 'text-[#10B981] mb-6' : 'text-[#002FD4] mb-6'} 
          />
          <h2 className="font-poppins font-bold text-[28px] leading-[36px] text-[#0F1011] mb-4">
            {getTitle()}
          </h2>
          <p className="font-poppins font-normal text-[16px] leading-[24px] text-[#64748B] max-w-[600px]">
            {getMessage()}
          </p>
        </div>
      </div>
    </div>
  )
}

export default AppointmentRequestSubmittedStep

