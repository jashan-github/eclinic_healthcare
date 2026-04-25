import { DatePickerInput } from '@mantine/dates'
import { useState, type FC, type ReactElement } from 'react'

const DateRangeDropdown: FC = (): ReactElement => {
  const [value, setValue] = useState<[string | null, string | null]>([
    null,
    null
  ])

  return (
    <DatePickerInput
      type="range"
      placeholder="Select a date range"
      value={value}
      onChange={setValue}
    />
  )
}

export default DateRangeDropdown
