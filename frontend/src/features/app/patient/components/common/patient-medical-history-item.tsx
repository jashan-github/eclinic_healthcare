import { ActionIcon, Badge, Flex, Text } from '@mantine/core'
import { TrashSimpleIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

interface PatientMedicalHistoryItemProps {
  id: string
  name: string
  disabled: boolean
  onDelete: (id: string) => void
}

const PatientMedicalHistoryItem: FC<PatientMedicalHistoryItemProps> = ({
  id,
  name,
  disabled,
  onDelete
}): ReactElement => (
  <Badge
    px="sm"
    py="sm"
    color={disabled ? 'gray.4' : 'red.4'}
    size="xs"
    variant="outline"
    key={id}
  >
    <Flex
      align="center"
      gap="xs"
      justify="space-between"
    >
      <Text
        className="capitalize"
        fw={400}
        size="sm"
      >
        {name}
      </Text>
      <ActionIcon
        color="red.4"
        disabled={disabled}
        size="sm"
        variant="transparent"
        onClick={() => onDelete(id)}
      >
        <TrashSimpleIcon weight="fill" />
      </ActionIcon>
    </Flex>
  </Badge>
)

export default PatientMedicalHistoryItem
