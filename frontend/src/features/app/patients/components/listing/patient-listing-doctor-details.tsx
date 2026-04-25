import { useMyProfile } from '@/features/app/my-profile/hooks/use-my-profile'
import {
  ActionIcon,
  Anchor,
  Badge,
  Card,
  CopyButton,
  Flex,
  Image,
  Mark,
  Stack,
  Text,
  Title
} from '@mantine/core'
import { CheckCircleIcon, CopyIcon, ShareFatIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const PatientListingDoctorDetails: FC = (): ReactElement => {
  const { myProfile } = useMyProfile()

  const copyValue = `Dr. ${myProfile.name} has invited you to eclinic.app. Use invite code ${myProfile.invite_code} or click here ${myProfile.invite_link} to consult with Dr. ${myProfile.name}. A connected healthcare experience awaits you on orvo.app.`

  return (
    <Card padding={'md'}>
      <Flex gap={'md'}>
        <Image
          src="/assets/icons/doctor-icon.svg"
          alt="Doctor Icon"
          h={80}
          fit="contain"
          w="auto"
        />
        <Stack gap={'xs'}>
          <Title order={3}>{myProfile?.name}</Title>
          {myProfile.major_specialization ? (
            <Text size={'xs'}>{myProfile.major_specialization}</Text>
          ) : (
            <Badge color="red.5">No Specialisation selected</Badge>
          )}

          <Text
            component="div"
            size={'xs'}
          >
            Invite Code:
            <Mark
              pl={4}
              color="white"
              className="font-bold"
            >
              {myProfile.invite_code}
            </Mark>
          </Text>
          <Text
            component="div"
            size={'xs'}
          >
            Invite Link:
            <Anchor
              href={myProfile.invite_link}
              target="_blank"
              pl={4}
              underline={'always'}
            >
              {myProfile.invite_link}
            </Anchor>
          </Text>
          <Flex gap={'md'}>
            <CopyButton value={copyValue}>
              {({ copied, copy }) => (
                <ActionIcon onClick={copy}>
                  {copied ? <CheckCircleIcon /> : <CopyIcon />}
                </ActionIcon>
              )}
            </CopyButton>
            <ActionIcon>
              <ShareFatIcon />
            </ActionIcon>
          </Flex>
        </Stack>
      </Flex>
    </Card>
  )
}

export default PatientListingDoctorDetails
