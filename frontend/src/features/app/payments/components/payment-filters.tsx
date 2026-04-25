// src/components/PaymentFilters.tsx
import { cn } from '@/lib/utils'
import { type FC, type ReactElement } from 'react'
import type { PaymentsStats } from '../services/payments-service'
import { formatFee } from '@/utils/helper'

interface PaymentFiltersProps {
  stats?: PaymentsStats
}

const PaymentFilters: FC<PaymentFiltersProps> = ({ stats }): ReactElement => {
  const totalEarned = stats?.total_earned ?? 0
  const currency = stats?.currency ?? 'USD'
  const growth = stats?.growth ?? 0
  const commission = 0;
  const paid = 0;

  console.log(growth)
  
  const boxClass = cn(
    'w-64 h-[102px] rounded-md border border-[#D1D1D1]',
    'flex flex-col justify-center items-start px-6 py-4',
    'bg-white'
  )

  return (
    <div className="flex items-center justify-start gap-6">

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Total Earned
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {`${formatFee(totalEarned, currency)}`}
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Commission Earned
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          ${commission}
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Growth
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {growth}%
        </div>
      </div>

      <div className={boxClass}>
        <div className="font-poppins font-semibold text-sm leading-none text-[#64748B] select-none">
          Total Referrals
        </div>
        <div className="font-poppins font-medium text-xl leading-7 text-[#0F1011] mt-1">
          {paid}
        </div>
      </div>
    </div>
  )
}

export default PaymentFilters
