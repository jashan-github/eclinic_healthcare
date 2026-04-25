import { cn } from '@/lib/utils'
import { type FC, type ReactElement } from 'react'
import { formatFee } from '@/utils/helper'

interface AnalyticsCardsProps {
  summary?: {
    total_patients: number
    total_appointments: number
    revenue: number
    total_waiver: number
    currency: string
  }
}

const AnalyticsCards: FC<AnalyticsCardsProps> = ({ summary }): ReactElement => {
    const boxClass = cn(
    'w-64 h-[102px] rounded-md border border-[#D1D1D1]',
    'flex flex-col justify-between items-start px-6 py-4',
    'bg-white'
  )

  // Fallback if no data yet
  if (!summary) {
    return (
      <div className="flex items-end justify-start gap-6 opacity-50">
        {/* Show skeleton or empty boxes */}
        <div className={boxClass}><div className="h-5 w-32 bg-gray-200 rounded"></div></div>
        <div className={boxClass}><div className="h-5 w-32 bg-gray-200 rounded"></div></div>
        <div className={boxClass}><div className="h-5 w-32 bg-gray-200 rounded"></div></div>
        <div className={boxClass}><div className="h-5 w-32 bg-gray-200 rounded"></div></div>
      </div>
    )
  }

  return (
    <div className="flex items-end justify-start gap-6">
      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Total Patients
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {summary.total_patients.toLocaleString()}
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Total Appointments
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {summary.total_appointments.toLocaleString()}
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Revenue
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {formatFee(summary.revenue, summary.currency)}
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Total Waiver
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {formatFee(summary.total_waiver, summary.currency)}
        </div>
      </div>
    </div>
  )
}

export default AnalyticsCards
