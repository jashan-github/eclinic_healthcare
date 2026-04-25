
import { ActionIcon, Menu } from '@mantine/core'
import {
  DotsThreeVerticalIcon
} from '@phosphor-icons/react'
import type { FC, ReactElement } from 'react'
import { useChatService } from '../../hooks/use-chat-service'
import type { Patient } from '../../services/patients-service'

interface PatientTableActionsProps {
  patient: Patient
}

const PatientTableActions: FC<PatientTableActionsProps> = ({
  patient
}): ReactElement => {
  const { createChat} = useChatService()
  const handleSendMessage = () => {
    if (patient && patient.id)
      createChat(patient.id)
  }

  // Don't show dropdown if it's an appointment request
  if (patient.is_appointment_request) {
    return <></>
  }

  return (
    <>
      <Menu
        shadow="md"
        width={250}
      >
        <Menu.Target>
          <ActionIcon variant="transparent">
            <DotsThreeVerticalIcon
              color="gray.9"
              size={20}
              weight="bold"
            />
          </ActionIcon>
        </Menu.Target>

        <Menu.Dropdown>
          <Menu.Item
            onClick={handleSendMessage}
          >
            Send Message
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </>
  )
}

export default PatientTableActions
