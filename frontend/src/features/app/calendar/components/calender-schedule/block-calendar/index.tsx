import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import { Skeleton, Stack } from '@mantine/core'
import { useState, type FC, type ReactElement } from 'react'
import { useBlockCalendarSlots } from '../../../hooks/use-block-calendar-slots'
import BlockCalendarAdd from './block-calendar-add'
import BlockCalendarItem from './block-calendar-item'

const BlockCalendar: FC = (): ReactElement => {
  const [isOpen, setIsOpen] = useState(false)
  const { blockedSlots, isLoading, error } = useBlockCalendarSlots()

  const toggleOpen = () => setIsOpen((prev) => !prev)

  return (
    <div className="flex h-full flex-col gap-4">
      <header>
        <h2 className="font-poppins text-base font-semibold text-[#0F1011]">
          Block Calendar
        </h2>
        <p className="font-poppins text-sm text-[#8D95B5]">
          Add dates when you won't be available as per your weekly calendar
        </p>
      </header>

      <button
        type="button"
        onClick={toggleOpen}
        className="w-full rounded-md border-2 border-[#002FD4] px-4 py-2 text-center font-poppins text-sm font-semibold text-[#002FD4] transition-colors hover:bg-[#002FD4]/5"
      >
        Select Dates
      </button>

      <div className="flex-1">
        {isLoading ? (
          <Stack gap="sm">
            <Skeleton height={40} />
            <Skeleton height={40} />
            <Skeleton height={40} />
          </Stack>
        ) : error ? (
          <ErrorWhileFetchingData width={50} />
        ) : (
          blockedSlots?.map((slot) => (
            <BlockCalendarItem
              key={slot.id}
              bookedSlot={slot}
            />
          ))
        )}
      </div>

      <BlockCalendarAdd
        isOpen={isOpen}
        setIsOpen={toggleOpen}
      />
    </div>
  )
}

export default BlockCalendar
