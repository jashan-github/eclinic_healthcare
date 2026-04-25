import { CalendarIcon, VideoCameraIcon } from '@phosphor-icons/react'

interface WebinarSummaryCardsProps {
  totalWebinars: number
  freeWebinars: number
  registeredWebinars: number
}

const WebinarSummaryCards = ({
  totalWebinars,
  freeWebinars,
  registeredWebinars
}: WebinarSummaryCardsProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Total Webinars */}
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
              Total Webinars
            </p>
            <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
              {totalWebinars}
            </p>
          </div>
          <div className="w-12 h-12 rounded-full  bg-opacity-10 flex items-center justify-center flex-shrink-0">
            <CalendarIcon size={24} weight="bold" color="#002FD4" />
          </div>
        </div>
      </div>

      {/* Free Webinars */}
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
              Free Webinars
            </p>
            <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
              {freeWebinars}
            </p>
          </div>
          <div className="w-12 h-12 rounded-full  bg-opacity-10 flex items-center justify-center flex-shrink-0">
            <VideoCameraIcon size={24} weight="bold" color="#002FD4" />
          </div>
        </div>
      </div>

      {/* Registered Webinars */}
      <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-2">
              Registered Webinars
            </p>
            <p className="font-poppins font-bold text-[32px] leading-[40px] text-[#0F1011]">
              {registeredWebinars}
            </p>
          </div>
          <div className="w-12 h-12 rounded-full  bg-opacity-10 flex items-center justify-center flex-shrink-0">
            <CalendarIcon size={24} weight="bold" color="#002FD4" />
          </div>
        </div>
      </div>
    </div>
  )
}

export default WebinarSummaryCards
