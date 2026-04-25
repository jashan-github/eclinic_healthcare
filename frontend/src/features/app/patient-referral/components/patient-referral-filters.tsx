import InformationCard from '@/components/orvo/information-card'
import { cn } from '@/lib/utils'
import { useState, type FC, type ReactElement } from 'react'

const FILTER_TYPE = {
  REFERRALS_GIVEN: 'referrals_given',
  REFERRAL_RECEIVED: 'referral_received'
} as const

type FilterType = typeof FILTER_TYPE
type FilterValue = FilterType[keyof FilterType]

const PatientReferralFilters: FC = (): ReactElement => {
  const [selectedFilter, setSelectedFilter] = useState<FilterValue>(
    FILTER_TYPE.REFERRALS_GIVEN
  )

  return (
    <div className="flex items-center justify-start gap-4">
      {/* Referrals Given */}
      <InformationCard
        title="Referrals Given"
        subtitle="-"
        className={cn(
          'border rounded flex flex-col items-start justify-center h-18 w-40 px-2 py-4 cursor-pointer',
          selectedFilter === FILTER_TYPE.REFERRALS_GIVEN
            ? 'border-primary'
            : 'border-gray-200'
        )}
        onCardClick={() => setSelectedFilter(FILTER_TYPE.REFERRALS_GIVEN)}
      />
      {/* Referral Received */}
      <InformationCard
        title="Referrals Received"
        subtitle="-"
        className={cn(
          'border rounded flex flex-col items-start justify-center h-18 w-40 px-2 py-4 cursor-pointer',
          selectedFilter === FILTER_TYPE.REFERRAL_RECEIVED
            ? 'border-primary'
            : 'border-gray-200'
        )}
        onCardClick={() => setSelectedFilter(FILTER_TYPE.REFERRAL_RECEIVED)}
      />
    </div>
  )
}

export default PatientReferralFilters
