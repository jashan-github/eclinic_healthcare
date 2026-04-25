import type { Patient } from '@/types/patient'
import {
  Button,
  Combobox,
  Flex,
  Grid,
  Modal,
  Select,
  Stack,
  Text,
  TextInput,
  useCombobox
} from '@mantine/core'
import { MagnifyingGlassIcon } from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'

// Dummy Data
const dummyDoctors: SelectedDoctor[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    specialization: 'Cardiology',
    phone_number: '+11234567890',
    clinic_id: 'c1'
  },
  {
    id: '2',
    name: 'Bob Lee',
    specialization: 'Neurology',
    phone_number: '+19876543210',
    clinic_id: 'c2'
  },
  {
    id: '3',
    name: 'Carol White',
    specialization: 'Pediatrics',
    phone_number: '+15551234567',
    clinic_id: 'c1'
  },
  {
    id: '4',
    name: 'David Kim',
    specialization: 'Orthopedics',
    phone_number: '+14449876543',
    clinic_id: 'c3'
  },
  {
    id: '5',
    name: 'Emma Brown',
    specialization: 'Dermatology',
    phone_number: '+13332221111',
    clinic_id: 'c2'
  },
  {
    id: '6',
    name: 'Frank Miller',
    specialization: 'General Practice',
    phone_number: '+17778889999',
    clinic_id: 'c4'
  }
]

interface ReferToADoctorProps {
  opened: boolean
  onClose: () => void
  patient: Patient
}

type SelectedDoctor = {
  id: string
  name: string
  specialization: string
  phone_number: string // could be mobile_number as well (TBD)
  clinic_id: string
}

const ReferToADoctor: FC<ReferToADoctorProps> = ({
  opened,
  onClose
}): ReactElement => {
  const combobox = useCombobox()

  const [value, setValue] = useState('')
  const [selectedDoctor, setSelectedDoctor] = useState<string | null>(null)
  const shouldFilterOptions = !dummyDoctors.some((item) => item.name === value)

  const filteredOptions = shouldFilterOptions
    ? dummyDoctors.filter((item) =>
        item.name.toLowerCase().includes(value.toLowerCase().trim())
      )
    : dummyDoctors

  const options = filteredOptions.map(({ id, name, specialization }) => (
    <Combobox.Option
      value={id}
      key={id}
    >
      <Stack gap={2}>
        <Text
          component="span"
          fw={600}
          size={'sm'}
        >
          {name}
        </Text>
        <Text
          c={'gray.7'}
          component="span"
          size={'xs'}
        >
          {specialization}
        </Text>
      </Stack>
    </Combobox.Option>
  ))

  return (
    <Modal
      closeOnClickOutside={false}
      onClose={onClose}
      opened={opened}
      size={'lg'}
      title={'Refer to a doctor'}
    >
      <Stack pt={'md'}>
        {selectedDoctor ? (
          <Stack>
            <Grid>
              <Grid.Col span={6}>
                <TextInput placeholder="Doctor name" />
              </Grid.Col>
              <Grid.Col span={6}>
                <TextInput
                  disabled
                  placeholder="Specialization"
                />
              </Grid.Col>
              <Grid.Col span={6}>
                <TextInput placeholder="Mobile number" />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  placeholder="Select Clinic"
                  data={['Demo Clinic One', 'Angular', 'Vue', 'Svelte']}
                />
              </Grid.Col>
            </Grid>
            <Flex
              gap={'sm'}
              justify={'flex-end'}
            >
              <Button
                onClick={() => {
                  setSelectedDoctor(null)
                  setValue('')
                }}
                variant={'outline'}
              >
                Cancel
              </Button>
              <Button>Add doctor</Button>
            </Flex>
          </Stack>
        ) : (
          <Combobox
            onOptionSubmit={(optionValue) => {
              setSelectedDoctor(optionValue)
              setValue(optionValue)
              combobox.closeDropdown()
            }}
            store={combobox}
          >
            <Combobox.Target>
              <TextInput
                leftSection={<MagnifyingGlassIcon />}
                placeholder="Start typing doctor name or speciality"
                value={value}
                onChange={(event) => {
                  setValue(event.currentTarget.value)
                  combobox.openDropdown()
                  combobox.updateSelectedOptionIndex()
                }}
                onClick={() => combobox.openDropdown()}
                onFocus={() => combobox.openDropdown()}
                onBlur={() => combobox.closeDropdown()}
              />
            </Combobox.Target>

            <Combobox.Dropdown>
              <Combobox.Options>
                {options.length === 0 ? (
                  <Combobox.Empty>Nothing found</Combobox.Empty>
                ) : (
                  options
                )}
              </Combobox.Options>
            </Combobox.Dropdown>
          </Combobox>
        )}
      </Stack>
    </Modal>
  )
}

export default ReferToADoctor
