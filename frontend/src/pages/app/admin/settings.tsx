import AdminSettingsTabs from '@/components/e-clinic/admin/settings/admin-settings-tabs'
import HeadSubhead from '@/components/ui/head-subhead'
import { type FC, type ReactElement } from 'react'

const SettingsPage: FC = (): ReactElement => {
  return (
    <div className="h-screen overflow-auto bg-[#F4F6F9]">
      <div className="p-6">
        <HeadSubhead
          head={'System Settings'}
          subhead={'Configure system preferences and notifications'}
        />
      </div>
      <div className='p-6 my-2'>
        <AdminSettingsTabs />
      </div>
    </div>
  )
}

export default SettingsPage