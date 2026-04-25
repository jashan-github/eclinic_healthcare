import { Button, Popover, Stack, Text } from '@mantine/core'
import { GearIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const PaymentColumnsFilters: FC = (): ReactElement => {
  return (
    <Popover withArrow>
      <Popover.Target>
        <Button
          variant="subtle"
          size="xs"
        >
          <GearIcon size={16} />
        </Button>
      </Popover.Target>
      <Popover.Dropdown className="w-[320px] h-[320px] border-gray-200">
        <Stack gap="md">
          <Text
            size="md"
            fw={500}
          >
            Column Settings
          </Text>
          <div className="h-[200px] overflow-y-scroll"></div>
          <Button>Apply Changes</Button>
        </Stack>
      </Popover.Dropdown>
    </Popover>
  )
}

export default PaymentColumnsFilters
