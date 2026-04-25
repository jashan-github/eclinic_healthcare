import { useState } from 'react'
import { Star } from '@phosphor-icons/react'
import Modal from '@/components/ui/modal'

interface RatingModalProps {
  isOpen: boolean
  onClose: () => void
  doctorName: string
  doctorSpecialty: string
  doctorImage: string
  onSubmit: (rating: number) => void
}

const RatingModal = ({
  isOpen,
  onClose,
  doctorName,
  doctorSpecialty,
  doctorImage,
  onSubmit
}: RatingModalProps) => {
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)

  const handleSubmit = () => {
    if (rating > 0) {
      onSubmit(rating)
      setRating(0)
      onClose()
    }
  }

  const handleCancel = () => {
    setRating(0)
    onClose()
  }

  const footer = (
    <>
      <button
        type="button"
        onClick={handleSubmit}
        disabled={rating === 0}
        className="px-6 py-2.5 bg-[#002FD4] hover:bg-[#001FB8] disabled:bg-[#E4E5ED] disabled:cursor-not-allowed 
          text-white font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors"
      >
        Submit
      </button>
      <button
        type="button"
        onClick={handleCancel}
        className="px-6 py-2.5 bg-white border border-[#002FD4] hover:bg-[#F4F6F9] text-[#002FD4] font-poppins font-semibold 
          text-[14px] leading-[20px] rounded-md transition-colors"
      >
        Cancel
      </button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      footer={footer}
      maxWidth="md"
      showCloseButton={false}
    >
      <div className="text-center">
        {/* Healthcare Provider Image */}
        <div className="flex justify-center mb-4">
          <img
            src={doctorImage}
            alt={doctorName}
            className="w-20 h-20 rounded-full object-cover border-4 border-[#F4F6F9]"
          />
        </div>

        {/* Healthcare Provider Name and Specialty */}
        <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011] mb-1">
          {doctorName}
        </h3>
        <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-6">
          {doctorSpecialty}
        </p>

        {/* Divider */}
        <div className="border-t border-[#E4E5ED] mb-6"></div>

        {/* Rating Question */}
        <p className="font-poppins font-normal text-[16px] leading-[24px] text-[#0F1011] mb-6">
          How was your experience with {doctorName}?
        </p>

        {/* Star Rating */}
        <div className="flex justify-center gap-2 mb-6">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoveredRating(star)}
              onMouseLeave={() => setHoveredRating(0)}
              className="focus:outline-none transition-transform hover:scale-110"
            >
              <Star
                size={32}
                weight={star <= (hoveredRating || rating) ? 'fill' : 'regular'}
                color={star <= (hoveredRating || rating) ? '#FFD700' : '#E4E5ED'}
              />
            </button>
          ))}
        </div>
      </div>
    </Modal>
  )
}

export default RatingModal

