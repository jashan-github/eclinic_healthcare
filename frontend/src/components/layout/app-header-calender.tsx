import { useAppStore } from '@/store/use-app-store'
import { Button } from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { CaretLeftIcon, CaretRightIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const AppHeaderCalender: FC = (): ReactElement => {
  const { selectedDate, setSelectedDate } = useAppStore()

  return (
    <Button.Group p={0}>
      <Button
        color="#E8EEFD"
        styles={{
          label: {
            color: '#002FD4'
          }
        }}
        variant={'filled'}
      >
        <CaretLeftIcon weight={'bold'} />
      </Button>
      <Button.GroupSection
        color="#E8EEFD"
        p={0}
        radius={0}
        variant={'filled'}
        miw={70}
      >
        <DatePickerInput
          onChange={setSelectedDate}
          placeholder="Select date"
          radius={0}
          styles={{
            input: {
              color: '#002FD4'
            }
          }}
          value={selectedDate}
          valueFormat="D MMM"
          variant={'unstyled'}
        />
      </Button.GroupSection>
      <Button
        color="#E8EEFD"
        styles={{
          label: {
            color: '#002FD4'
          }
        }}
        variant={'filled'}
      >
        <CaretRightIcon weight={'bold'} />
      </Button>
    </Button.Group>
  )
}

export default AppHeaderCalender
