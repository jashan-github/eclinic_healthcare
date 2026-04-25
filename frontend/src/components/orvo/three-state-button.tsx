import { ActionIcon, Flex, Text } from '@mantine/core'
import { CaretUpDownIcon } from '@phosphor-icons/react'
import { useEffect, useState, type ReactElement } from 'react'

export interface ThreeStateButtonProps<
  TPositive extends string,
  TNegative extends string,
  TIndeterminate extends string
> {
  label: string
  initialValue?: TPositive | TNegative | TIndeterminate
  positive: TPositive
  negative: TNegative
  indeterminate: TIndeterminate
  onValueChange: (val: TPositive | TNegative | TIndeterminate) => void
}

export type ThreeStateButtonValue<T> = T extends {
  positive: infer P extends string
  negative: infer N extends string
  indeterminate: infer I extends string
}
  ? P | N | I
  : never

export const ThreeStateButton = <
  TPositive extends string,
  TNegative extends string,
  TIndeterminate extends string
>({
  label,
  initialValue,
  onValueChange,
  positive,
  negative,
  indeterminate
}: ThreeStateButtonProps<
  TPositive,
  TNegative,
  TIndeterminate
>): ReactElement => {
  type State = TPositive | TNegative | TIndeterminate

  const [state, setState] = useState<State>(initialValue ?? indeterminate)

  useEffect(() => {
    setState(initialValue ?? indeterminate)
  }, [initialValue, indeterminate])

  const toggleState = () => {
    setState((prev) => {
      if (prev === positive) return negative
      if (prev === negative) return indeterminate
      return positive
    })
  }

  // Only notify parent after the state change is fully applied
  useEffect(() => {
    onValueChange(state)
  }, [state, onValueChange])

  return (
    <Flex
      align="center"
      gap="xs"
    >
      <ActionIcon
        aria-label={`${label}: ${state}`}
        color={
          state === positive ? 'green' : state === negative ? 'red' : 'gray'
        }
        onClick={toggleState}
        radius="xl"
        size="xl"
        variant="outline"
      >
        <Flex
          align="center"
          gap={4}
        >
          <Text fw={700}>
            {state === positive ? 'Y' : state === negative ? 'N' : '-'}
          </Text>
          <CaretUpDownIcon size={14} />
        </Flex>
      </ActionIcon>
      <Text
        fw={600}
        size="xs"
      >
        {label}
      </Text>
    </Flex>
  )
}
