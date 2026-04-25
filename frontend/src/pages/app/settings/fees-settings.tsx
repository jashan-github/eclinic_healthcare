import FeesSettingsContent from '@/features/app/settings/components/fees-settings-content'
import { type FC, type ReactElement } from 'react'

const FeesSettings: FC = (): ReactElement => {

  return (
    <div className="p-6">
        <FeesSettingsContent />
    </div>
  )
}

export default FeesSettings
