// components/calendar/block-calendar-item.tsx

import type { TimeOffItem } from '@/types/calendar'
import { ActionIcon, Grid, Text } from '@mantine/core'
import { TrashSimpleIcon } from '@phosphor-icons/react'
import { format, parseISO } from 'date-fns'
import { memo, useMemo } from 'react'
import { useBlockCalendarSlots } from '../../../hooks/use-block-calendar-slots'

const formatDate = (date: string): string => {
  if (!date) return ''
  const parsed = parseISO(date)
  return `${format(parsed, 'dd MMM')}'${format(parsed, 'yy')}`
}

const formatTime12 = (dateTime: string): string => {
  if (!dateTime) return ''
  const parsed = parseISO(dateTime)
  return format(parsed, 'h:mm a')
}

const BlockCalendarItem = memo(({ bookedSlot }: { bookedSlot: TimeOffItem }) => {
  const { id, start_datetime, end_datetime, reason } = bookedSlot

  const { deleteBlockedSlot, isDeleting } = useBlockCalendarSlots()

  // Check if it's an entire day (00:00 to 23:59)
  const isEntireDay = useMemo(() => {
    const start = parseISO(start_datetime)
    const end = parseISO(end_datetime)
    const startTime = format(start, 'HH:mm')
    const endTime = format(end, 'HH:mm')
    return startTime === '00:00' && endTime === '23:59'
  }, [start_datetime, end_datetime])

  // Check if start and end are on the same day (normalize to avoid timezone issues)
  const isSameDay = useMemo(() => {
    try {
      // Extract just the date part (YYYY-MM-DD) from ISO strings to avoid timezone issues
      const startDateStr = start_datetime.split('T')[0]
      const endDateStr = end_datetime.split('T')[0]
      
      // Compare date strings directly
      return startDateStr === endDateStr
    } catch (error) {
      // Fallback to date comparison if parsing fails
      const start = parseISO(start_datetime)
      const end = parseISO(end_datetime)
      const startNormalized = new Date(start.getFullYear(), start.getMonth(), start.getDate())
      const endNormalized = new Date(end.getFullYear(), end.getMonth(), end.getDate())
      return startNormalized.getTime() === endNormalized.getTime()
    }
  }, [start_datetime, end_datetime])

  const dates = useMemo(
    () => ({
      start: formatDate(start_datetime),
      end: isSameDay ? '' : formatDate(end_datetime),
    }),
    [start_datetime, end_datetime, isSameDay]
  )

  const timeRange = useMemo(() => {
    if (isEntireDay) return 'All Day'
    const start = formatTime12(start_datetime)
    const end = formatTime12(end_datetime)
    return `${start} - ${end}`
  }, [start_datetime, end_datetime, isEntireDay])

  const onDeleteClicked = () => {
    if (isDeleting) return // Prevent double click
    deleteBlockedSlot(id)
  }

  return (
    <Grid
      gutter="xs"
      className="py-2 hover:bg-gray-50 transition-colors"
      style={{
        borderTop: '1px solid #E4E5ED',
        borderBottom: '1px solid #E4E5ED',
      }}
    >
      <Grid.Col span={4}>
        <Text style={{ fontFamily: 'Poppins', fontWeight: 600, fontSize: '14px', color: '#0F1011' }}>
          {isSameDay ? dates.start : `${dates.start} - ${dates.end}`}
        </Text>
      </Grid.Col>

      <Grid.Col span={6}>
        <Text style={{ fontFamily: 'Poppins', fontWeight: 400, fontSize: '14px', color: '#0F1011' }}>
          {timeRange}
          {reason && (
            <span style={{ marginLeft: '8px', color: '#64748B', fontSize: '12px' }}>
              ({reason})
            </span>
          )}
        </Text>
      </Grid.Col>

      <Grid.Col span={2}>
        <ActionIcon
          color="black"
          variant="subtle"
          onClick={onDeleteClicked}
        >
          <TrashSimpleIcon size={20} />
        </ActionIcon>
      </Grid.Col>
    </Grid>
  )
})

BlockCalendarItem.displayName = 'BlockCalendarItem'

export default BlockCalendarItem