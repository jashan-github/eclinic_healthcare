import AppGlobalSearch from '@/components/layout/app-global-search'
import { useHeaderStore } from '@/store/use-header-store'
import { useRouterState } from '@tanstack/react-router'
import { useEffect, useState, type FC, type ReactElement } from 'react'
import AppAppointmentViewSwitcher from './app-appointment-view-switcher'
// import AppHeaderCalender from './app-header-calender'
import AppHeaderUserSettingsDropdown from './app-header-user-settings-dropdown'

const AppHeader: FC = (): ReactElement => {
  const { pageTitle } = useHeaderStore()

  const router = useRouterState()

  // const [showAppGlobalSearch, setShowAppGlobalSearch] = useState(false)
  // const [showAppointmentCalendar, setShowAppointmentCalendar] = useState(false)
  const [showAppointmentViewSwitcher, setShowAppointmentViewSwitcher] =
    useState(false)

  useEffect(() => {
    // setShowAppGlobalSearch(
    //   ['/app/appointments', '/app/patients', '/app/settings'].includes(router.location.pathname)
    // )

    // setShowAppointmentCalendar(
    //   ['/app/appointments'].includes(router.location.pathname)
    // )

    setShowAppointmentViewSwitcher(
      ['/app/appointments'].includes(router.location.pathname)
    )
  }, [router.location.pathname])

  return (
    <div className="border-b border-gray-200 px-4 flex gap-2 justify-between bg-white items-center h-[60px] w-full">
      <div className="flex h-[60px] items-center gap-2 shrink">
        <div className="font-medium text-xl">{pageTitle || 'Salutogena'}</div>
      </div>

      <div className="flex grow h-[60px] justify-between items-center">
        {/* Left Side Content */}
        <div className="flex items-center gap-2">
          {/* {showAppointmentCalendar && <AppHeaderCalender />} */}

          {showAppointmentViewSwitcher && <AppAppointmentViewSwitcher />}
        </div>

        {/* Right Side Content */}
        <div className="flex items-center gap-2">
          {/* {showAppGlobalSearch && <AppGlobalSearch />} */}
          <AppGlobalSearch />
        </div>
      </div>

      <div className="flex h-[60px] items-center gap-2 shrink">
        <AppHeaderUserSettingsDropdown />
      </div>
    </div>
  )
}

export default AppHeader
