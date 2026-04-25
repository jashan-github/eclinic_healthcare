import DateRangeDropdown from '@/components/orvo/common/date-range-dropdown'
import DateRangePresetsDropdown from '@/components/orvo/common/date-range-presets-dropdown'
import { ActionIcon } from '@mantine/core'
import { GearIcon } from '@phosphor-icons/react'

import { type FC, type ReactElement } from 'react'

const PaymentsHeader: FC = (): ReactElement => {
  return (
    <div className="flex items-center gap-2">
      {/* Edit Receipt Template Button */}
      <ActionIcon variant={'transparent'}>
        <GearIcon
          size={20}
          weight={'fill'}
        />
      </ActionIcon>

      {/* Date Range Presets dropdown */}
      <DateRangePresetsDropdown />
      {/* Date Range Selector */}
      <DateRangeDropdown />
    </div>
  )
}

export default PaymentsHeader
