import { Chip, Group } from '@mantine/core'
import { XIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

const dummySelectedLabTests = [
  {
    id: 1,
    label: 'CBC',
    value: 'cbc'
  },
  {
    id: 1,
    label: 'Total cholesterol',
    value: 'cbc'
  },
  {
    id: 1,
    label: 'C-Reactive Protein (CRP)',
    value: 'cbc'
  }
]

const SelectedLabTests: FC = (): ReactElement => {
  const removeSelectedTest = (id: string | number) => {
    console.log(id)
  }
  return (
    <Group gap={'sm'}>
      {dummySelectedLabTests &&
        dummySelectedLabTests.map(({ id, label }) => (
          <Chip
            checked={true}
            key={id}
            icon={
              <XIcon
                onClick={() => removeSelectedTest(id)}
                size={16}
              />
            }
            color="primary"
            variant="light"
            defaultChecked
            onClick={() => null}
            onChange={() => null}
          >
            {label}
          </Chip>
        ))}
    </Group>
  )
}

export default SelectedLabTests
