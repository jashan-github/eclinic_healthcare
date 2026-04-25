import AppointmentSettings from '@/components/e-clinic/admin/settings/appointment-settings'
import GeneralSettings from '@/components/e-clinic/admin/settings/general-settings'
import { type FC, type ReactElement } from 'react'

const AdminGeneralSettingsPage: FC = (): ReactElement => {
  return (
    <div className="p-6 space-y-4">
      <GeneralSettings />
      <AppointmentSettings />
    </div>
  )
}

export default AdminGeneralSettingsPage

