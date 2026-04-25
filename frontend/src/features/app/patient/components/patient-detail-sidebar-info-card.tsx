import {
  Anchor,
  Avatar,
  Divider,
  Flex,
  Skeleton,
  Stack,
  Text
} from '@mantine/core'
import { NotePencilIcon } from '@phosphor-icons/react'
import { useLocation } from '@tanstack/react-router'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'

const PatientDetailSidebarInfoCard: FC = (): ReactElement => {
  const { pathname } = useLocation()

  const isNewPatient = pathname === '/app/patient/new'

  if (isNewPatient) {
    return (
      <Stack p={'sm'}>
        <Skeleton
          h={80}
          width={'100%'}
        />
      </Stack>
    )
  }

  return (
    <Stack
      gap={0}
      pb={'md'}
    >
      <Flex
        justify={'space-between'}
        p={'sm'}
      >
        <Stack gap={2}>
          <Avatar
            radius={'xl'}
            size={60}
          />

          <Text
            c="gray.8"
            fw={800}
          >
            John Doe
          </Text>
          <Flex
            c="gray.7"
            gap={2}
            justify={'flex-start'}
          >
            <Text size={'xs'}>5Y</Text>
            <Divider
              size={'sm'}
              orientation={'vertical'}
            />
            <Text size={'xs'}>M</Text>
            <Divider
              size={'sm'}
              orientation={'vertical'}
            />
            <Text size={'xs'}>#JD100005</Text>
          </Flex>
          <Text
            c="gray.7"
            size={'xs'}
          >
            +91-8123565698
          </Text>
        </Stack>

        <Anchor onClick={() => toast.info('Coming Soon...')}>
          <Flex
            gap={3}
            align={'center'}
          >
            <NotePencilIcon size={20} />
            <Text
              fw={600}
              size={'sm'}
            >
              Edit
            </Text>
          </Flex>
        </Anchor>
      </Flex>

      {/* Merge Patients wrapper */}
      <Flex px={'sm'}>
        <Anchor
          c={'primary'}
          fw={700}
          onClick={() => toast.info('Coming soon...')}
          size={'sm'}
        >
          Merge Patients
        </Anchor>
      </Flex>
    </Stack>
  )
}

export default PatientDetailSidebarInfoCard
