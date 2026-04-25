import {
  Avatar,
  Button,
  Divider,
  Flex,
  Modal,
  Paper,
  Stack,
  Title
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { MapPinIcon, MapTrifoldIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const AddAddressModal = () => {
  const [opened, handlers] = useDisclosure(false)
  return (
    <>
      <Modal
        opened={opened}
        onClose={handlers.close}
        title="Authentication"
      >
        {/* Modal content */}
      </Modal>

      <Button
        variant="default"
        onClick={handlers.open}
      >
        Open modal
      </Button>
    </>
  )
}

const LabTestPatientAddress: FC = (): ReactElement => {
  return (
    <Paper>
      <Stack p={'sm'}>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'flex-start'}
        >
          <Avatar
            bg={'#EC6657'}
            color="#fff"
            radius={'sm'}
            size={'sm'}
          >
            <MapPinIcon
              size={20}
              weight={'fill'}
            />
          </Avatar>
          <Title order={6}>Patient Address</Title>
        </Flex>
      </Stack>
      <Divider />
      <Stack>
        <Flex justify={'center'}>
          <MapTrifoldIcon
            size={64}
            weight={'duotone'}
          />
        </Flex>
        <AddAddressModal />
      </Stack>
    </Paper>
  )
}

export default LabTestPatientAddress
