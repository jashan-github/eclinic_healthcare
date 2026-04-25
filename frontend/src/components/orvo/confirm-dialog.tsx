import { useState, type FC, type ReactElement } from 'react'
import { Button, Group, Modal, Text, Title } from '@mantine/core'
import { TrashIcon } from '@phosphor-icons/react'

interface ConfirmDialogProps {
  title: string
  description: string
  disabled: boolean
  cancelLabel?: string
  confirmLabel?: string
  onClickConfirm: () => void
}

const ConfirmDialog: FC<ConfirmDialogProps> = ({
  title = '',
  description = '',
  disabled,
  cancelLabel = 'Cancel',
  confirmLabel = 'Confirm',
  onClickConfirm
}): ReactElement => {
  const [opened, setOpened] = useState(false)

  return (
    <>
      <Button
        variant="subtle"
        size="xs"
        disabled={disabled}
        aria-label={title}
        onClick={() => setOpened(true)}
        leftSection={<TrashIcon size={16} />}
      />
      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title={<Title order={4}>{title}</Title>}
        centered
        size="sm"
      >
        <Text
          size="sm"
          mb="lg"
        >
          {description}
        </Text>
        <Group justify="flex-end">
          <Button
            variant="default"
            onClick={() => setOpened(false)}
          >
            {cancelLabel}
          </Button>
          <Button
            color="red"
            onClick={() => {
              onClickConfirm()
              setOpened(false)
            }}
          >
            {confirmLabel}
          </Button>
        </Group>
      </Modal>
    </>
  )
}

export default ConfirmDialog
