import StaffRestrictionsContent from '@/features/app/settings/components/staff-restrictions-content'
import { type FC, type ReactElement } from 'react'

const StaffRestrictions: FC = (): ReactElement => {

  return (
    <div className="p-6">
        <StaffRestrictionsContent />
    </div>
  )
}

export default StaffRestrictions
