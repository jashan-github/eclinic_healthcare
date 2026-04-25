import type { Patient } from '@/types/patient'
import { Modal, Stack, Stepper } from '@mantine/core'
import { useState, type FC, type ReactElement } from 'react'

interface CreateAbhaProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

const CreateAbha: FC<CreateAbhaProps> = ({ opened, onClose }): ReactElement => {
  const [active, setActive] = useState(1)

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      size={'lg'}
      title={'Create ABHA'}
    >
      <Stack
        gap={'md'}
        pt={'xl'}
      >
        <Stepper
          active={active}
          onStepClick={setActive}
          size={'xs'}
        >
          <Stepper.Step>ABHA Step 1</Stepper.Step>
          <Stepper.Step>ABHA Step 2</Stepper.Step>
          <Stepper.Step>ABHA Step 3</Stepper.Step>
        </Stepper>
      </Stack>
    </Modal>
  )
}

export default CreateAbha
