import { type FC, type ReactElement } from 'react'
import { Text } from '@mantine/core'

interface CustomFieldLabelProps {
  fontWeight?: number
  label: string
  isRequired?: boolean
}

const CustomFieldLabel: FC<CustomFieldLabelProps> = ({
  fontWeight = 500,
  label,
  isRequired = true
}): ReactElement => {
  return (
    <Text
      fw={fontWeight}
      size={'sm'}
    >
      {label} {isRequired && <sup className="text-red">*</sup>}
    </Text>
  )
}

export default CustomFieldLabel
