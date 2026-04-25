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
import { MapTrifoldIcon, PhoneIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const UpdateRecipientContact: FC = (): ReactElement => {
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

const LabTestRecipientContact: FC = (): ReactElement => {
  return (
    <Paper>
      <Stack p={'sm'}>
        <Flex
          align={'center'}
          gap={'sm'}
          justify={'flex-start'}
        >
          <Avatar
            bg={'#edae0a'}
            color="#fff"
            radius={'sm'}
            size={'sm'}
          >
            <PhoneIcon
              size={20}
              weight={'fill'}
            />
          </Avatar>
          <Title order={6}>Recipient Contact</Title>
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
        <UpdateRecipientContact />
      </Stack>
    </Paper>
  )
}

export default LabTestRecipientContact
