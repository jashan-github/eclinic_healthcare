import { Select } from '@mantine/core'
import { CaretDownIcon } from '@phosphor-icons/react'
import { type FC } from 'react'

interface BaseTimePicker {
  value: string | null
  interval?: string
  startTime?: string
  endTime?: string
  onSelect: (value: string | null) => void
}

const BaseTimePicker: FC<BaseTimePicker> = ({
  value,
  onSelect,
  startTime = '09:00',
  endTime = '23:45',
  interval = '00:15'
}) => {
  const generateTimeOptions = () => {
    const options: string[] = []
    let current = new Date(`2000-01-01 ${startTime}`)
    const end = new Date(`2000-01-01 ${endTime}`)

    const [h, m] = interval.split(':').map(Number)
    const intervalMs = (h * 60 + m) * 60 * 1000

    while (current <= end) {
      options.push(current.toTimeString().slice(0, 5))
      current = new Date(current.getTime() + intervalMs)
    }
    return options
  }

  const data = generateTimeOptions().map((time) => {
    const [h, m] = time.split(':').map(Number)
    const hour = h % 12 || 12
    const ampm = h < 12 ? 'am' : 'pm'
    return {
      value: time,
      label: `${hour}:${m.toString().padStart(2, '0')} ${ampm}`
    }
  })

  return (
    <Select
      className="rounded-lg"
      data={data}
      onChange={onSelect}
      placeholder="Select time"
      rightSection={
        <CaretDownIcon
          color="#000"
          weight={'bold'}
        />
      }
      searchable
      styles={{
        input: {
          border: '1px solid #0F1011',
          borderRadius: '8px',
          height: '40px'
        }
      }}
      value={value}
    />
  )
}

export default BaseTimePicker
