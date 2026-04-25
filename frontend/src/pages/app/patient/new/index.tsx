import PatientConfigurationModal from '@/features/app/patient/components/common/patient-configuration-modal'
import NewPatientForm from '@/features/app/patient/components/new'
import {
  ActionIcon,
  Card,
  Flex,
  ScrollArea,
  Stack,
  Text,
  Title
} from '@mantine/core'
import { useElementSize } from '@mantine/hooks'
import { GearSixIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

const NewPatientPage: FC = (): ReactElement => {
  const { ref, height } = useElementSize()
  const [showPatientConfigurationModal, setShowPatientConfigurationModal] =
    useState(false)

  return (
    <Stack
      ref={ref}
      gap={0}
      h={'100vh'}
    >
      <Flex
        bg={'white'}
        px={'md'}
        h={60}
        justify={'space-between'}
        align={'center'}
      >
        <Title order={5}>Add New Patient</Title>

        <Flex
          align={'center'}
          gap={0}
        >
          <ActionIcon
            onClick={() => setShowPatientConfigurationModal(true)}
            radius={'xl'}
            size={'lg'}
            variant={'transparent'}
          >
            <GearSixIcon weight={'fill'} />
          </ActionIcon>
          <Text
            className="cursor-pointer"
            fw={600}
            onClick={() => setShowPatientConfigurationModal(true)}
            size={'sm'}
          >
            Configure
          </Text>
        </Flex>
      </Flex>

      <Card
        h={height - 60}
        radius={0}
        padding={'md'}
        bg={'gray.2'}
      >
        <Card
          h={'100%'}
          withBorder
          radius={'md'}
        >
          <ScrollArea
            h={'100%'}
            w={'100%'}
            scrollbars="y"
          >
            <NewPatientForm
              openConfigureModal={setShowPatientConfigurationModal}
            />
          </ScrollArea>
        </Card>
      </Card>
      <PatientConfigurationModal
        isOpen={showPatientConfigurationModal}
        setIsOpen={setShowPatientConfigurationModal}
      />
    </Stack>
  )
}

export default NewPatientPage
