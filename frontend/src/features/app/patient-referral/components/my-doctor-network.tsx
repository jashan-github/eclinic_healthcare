import { Button, Drawer, Group, Stack, Text } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import PatientReferralTable from './patient-referral-table'

type MyDoctorNetworkProps = {
  isOpen: boolean
  onClose: () => void
}

const MyDoctorNetwork: FC<MyDoctorNetworkProps> = ({
  isOpen = false,
  onClose
}): ReactElement => {
  return (
    <Drawer
      opened={isOpen}
      onClose={onClose}
      position="right"
      size="80vw"
      styles={{
        content: {
          maxWidth: 'var(--mantine-breakpoint-7xl)',
          border: '1px solid #e5e7eb'
        },
        header: { backgroundColor: '#f3f4f6' }
      }}
    >
      <Stack gap={0}>
        <Text
          size="lg"
          fw={500}
          p="md"
        >
          Healthcare Provider Network
        </Text>
        <PatientReferralTable />
        <Group
          justify="flex-end"
          p="md"
        >
          <Button
            onClick={onClose}
            style={{ minWidth: 'fit-content', maxWidth: '200px' }}
          >
            Cancel
          </Button>
        </Group>
      </Stack>
    </Drawer>
  )
}

export default MyDoctorNetwork
