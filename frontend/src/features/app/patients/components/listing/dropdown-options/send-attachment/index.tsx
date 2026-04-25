import type { Patient } from '@/types/patient'
import {
  Button,
  Flex,
  Modal,
  Stack,
  Tabs,
  Text,
  Textarea,
  TextInput
} from '@mantine/core'
import { Dropzone } from '@mantine/dropzone'
import { UploadSimpleIcon } from '@phosphor-icons/react'
import { useRef, type FC, type ReactElement } from 'react'

interface SendAttachmentProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const SendAttachment: FC<SendAttachmentProps> = ({
  opened,
  onClose
}): ReactElement => {
  const openRef = useRef<() => void>(null)

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size={'lg'}
      withCloseButton={false}
    >
      <Tabs
        defaultValue="send-files"
        variant={'outline'}
      >
        <Tabs.List>
          <Tabs.Tab value="send-files">SEND FILES</Tabs.Tab>
          <Tabs.Tab value="templates">TEMPLATES</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="send-files">
          <Stack
            gap={'xl'}
            mt={'md'}
          >
            <TextInput
              label={'Title'}
              placeholder={'Add your title here'}
              withAsterisk
            />
            <Textarea
              label={'Note'}
              rows={5}
              placeholder={'Add your note here'}
            />
            <Flex
              align={'flex-start'}
              direction={'column'}
              gap={2}
              justify={'flex-start'}
            >
              <Text
                fw={500}
                size={'sm'}
              >
                Attach File
              </Text>
              <Dropzone
                activateOnClick={false}
                acceptColor="primary"
                onDrop={() => {}}
                openRef={openRef}
                p={0}
              >
                <Button
                  leftSection={<UploadSimpleIcon />}
                  onClick={() => openRef.current?.()}
                  style={{ pointerEvents: 'all' }}
                  variant={'transparent'}
                >
                  Upload File
                </Button>
              </Dropzone>
            </Flex>
            <Flex
              gap={'sm'}
              justify={'flex-end'}
            >
              <Button
                onClick={onClose}
                variant={'outline'}
              >
                Cancel
              </Button>
              <Button>Send</Button>
            </Flex>
          </Stack>
        </Tabs.Panel>
        <Tabs.Panel value="templates">
          <Flex
            h={200}
            align={'center'}
            justify={'center'}
          >
            <Text>No Templates Added...</Text>
          </Flex>
        </Tabs.Panel>
      </Tabs>
    </Modal>
  )
}

export default SendAttachment
