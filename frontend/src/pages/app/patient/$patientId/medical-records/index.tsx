import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Divider,
  Flex,
  Group,
  Paper,
  ScrollArea,
  Stack,
  Tabs,
  Text
} from '@mantine/core'
import {
  ArrowsClockwiseIcon,
  CloudIcon,
  FileIcon,
  UploadIcon
} from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'

const MedicalRecords: FC = (): ReactElement => {
  return (
    <Stack
      h={'100vh'}
      gap={0}
    >
      {/* Header */}
      <Box
        h={60}
        bg={'white'}
        px={'sm'}
        w={'100%'}
      >
        <Flex
          h={60}
          w={'100%'}
          align={'center'}
          justify={'space-between'}
        >
          <Group gap={'xs'}>
            <Text
              component="div"
              fw={500}
            >
              Patient Medical History
            </Text>
            <ActionIcon
              onClick={() => toast.info('Updating medical history...')}
              variant={'transparent'}
            >
              <ArrowsClockwiseIcon
                size={20}
                weight={'bold'}
              />
            </ActionIcon>
          </Group>

          <Button
            rightSection={
              <UploadIcon
                size={20}
                weight={'fill'}
              />
            }
          >
            Upload
          </Button>
        </Flex>
      </Box>
      <Divider />
      <ScrollArea h={'100vh-60px'}>
        <Tabs defaultValue="my-records">
          <Tabs.List justify={'flex-start'}>
            <Flex
              align={'center'}
              justify={'space-between'}
              bg={'white'}
              px={'md'}
              w={'100%'}
            >
              <Group>
                <Tabs.Tab
                  value="my-records"
                  leftSection={
                    <FileIcon
                      size={20}
                      weight={'fill'}
                    />
                  }
                >
                  My Records
                </Tabs.Tab>
                <Tabs.Tab
                  value="abha-requests"
                  leftSection={
                    <FileIcon
                      size={20}
                      weight={'fill'}
                    />
                  }
                >
                  ABHA Requests
                </Tabs.Tab>
              </Group>
              <Badge
                color="green.1"
                py={'sm'}
                radius={'md'}
              >
                <Group gap={'xs'}>
                  <CloudIcon
                    color="green"
                    size={20}
                    weight={'fill'}
                  />
                  <Text
                    size={'xs'}
                    c="gray.8"
                    className="capitalize"
                  >
                    Storage:
                  </Text>
                  <Text
                    fw={600}
                    size={'xs'}
                    c="darkgreen"
                    className="capitalize"
                  >
                    0MB of patient data stored
                  </Text>
                </Group>
              </Badge>
            </Flex>
          </Tabs.List>

          <Tabs.Panel value="my-records">
            <Stack p={'md'}>
              <Paper p={'md'}>
                <Text>No records found!!</Text>
              </Paper>
            </Stack>
          </Tabs.Panel>

          <Tabs.Panel value="abha-requests">
            <Stack p={'md'}>
              <Paper p={'md'}>
                <Text>No records found!!</Text>
              </Paper>
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </ScrollArea>
    </Stack>
  )
}

export default MedicalRecords
