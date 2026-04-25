import { useViewStore } from '@/context/view-context/view-context'
import { SegmentedControl } from '@mantine/core'
import { CalendarBlankIcon, ListIcon } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'

const AppAppointmentViewSwitcher = () => {
  const [value, setValue] = useState('list')
  const setViewInStore = useViewStore((s) => s.setView)
  useEffect(() => {
    setViewInStore(value as 'list' | 'calendar')
  }, [value, setViewInStore])
  return (
    <SegmentedControl
      data={[
        {
          label: (
            <div className="flex items-center gap-2">
              <ListIcon size={20} color={value === 'list' ? '#002FD4' : '#000000'} />
              {value === 'list' && (
                <div className="font-poppins font-normal text-sm leading-5 text-[#0F1011]">List View</div>
              )}
            </div>
          ),
          value: 'list'
        },
        {
          label: (
            <div className="flex items-center gap-2">
              <CalendarBlankIcon size={20} color={value === 'calendar' ? '#002FD4' : '#000000'} />
              {value === 'calendar' && (
                <div className="font-poppins font-normal text-sm leading-5 text-[#0F1011]">Calendar View</div>
              )}
            </div>
          ),
          value: 'calendar'
        }
      ]}
      value={value}
      onChange={setValue}
      size={'md'}
    />
  )
}

export default AppAppointmentViewSwitcher
