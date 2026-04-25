import SettingsSidebar from '@/components/layout/settings-sidebar'
import { useHeaderStore } from '@/store/use-header-store'
import { Outlet } from '@tanstack/react-router'
import { useEffect, type FC, type ReactElement } from 'react'

const SettingsLayout: FC = (): ReactElement => {
  const { setPageTitle } = useHeaderStore()

  useEffect(() => {
    setPageTitle('Settings and preferences')
  }, [setPageTitle])

  return (
    <div className="flex flex-col bg-[#F4F6F9] gap-0 h-screen">
      <div className="flex gap-0 h-full">
        <SettingsSidebar />
        <div className="bg-[#F4F6F9] h-full w-full overflow-y-auto">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export default SettingsLayout
