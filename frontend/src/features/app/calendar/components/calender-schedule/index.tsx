import { type FC, type ReactElement } from 'react'
import BlockCalendar from './block-calendar'
import WeeklySchedule from './weekly-schedule'
// import { FloppyDiskIcon } from '@phosphor-icons/react'

const CalendarSchedule: FC = (): ReactElement => {
  // const [hasChanges, setHasChanges] = useState(false)
  return (
    <div>
      <div className="flex gap-6 max-w-[90%] mx-auto bg-white rounded-2xl p-6 shadow-[6px_7px_20px_0px_#0000001A] overflow-hidden">
        <div style={{ flex: '1 1 70%' }}>
          <WeeklySchedule />
          {/* <WeeklySchedule onChange={setHasChanges} /> */}
        </div>

        <div className="w-0.5 bg-[#E4E5ED] self-stretch m-0" />

        <div className="flex-1 min-w-[30%]">
          <BlockCalendar />
        </div>
      </div>
        {/* {hasChanges && (
        <div className="-translate-y-8 py-2 bg-[#002FD4] rounded-md mx-auto max-w-[85%] flex items-center justify-between px-6 shadow-lg">
          <button 
            className="mx-auto bg-white text-[#002FD4] font-semibold px-3 py-1 rounded-sm flex items-center gap-2 hover:bg-gray-50 transition-all shadow-md hover:cursor-pointer"
            onClick={() => {
              setHasChanges(false)
            }}
          >
            <FloppyDiskIcon size={20} weight="bold" />
            Save Changes
          </button>
        </div>
      )} */}
      </div>
  )
}

export default CalendarSchedule
