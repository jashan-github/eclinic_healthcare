import { useMedicalHistory } from '@/hooks/use-medical-history'
import type { MedicalHistory } from '@/types/medical-history'
import {
  Alert,
  Button,
  Card,
  Flex,
  Group,
  Loader,
  Radio,
  Select,
  Skeleton,
  Stack,
  Switch,
  Text
} from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { MagnifyingGlassIcon, WarningCircleIcon } from '@phosphor-icons/react'
import { useForm, useStore } from '@tanstack/react-form'
import { isEqual } from 'lodash'
import { useEffect, useMemo, useState, type FC, type ReactElement } from 'react'
import { usePatientMedicalHistory } from '../../hooks/use-patient-medical-history'
import PatientMedicalHistoryItem from './patient-medical-history-item'

const MEDICAL_HISTORY_TYPES = [
  { label: 'Condition', value: 'conditions' },
  { label: 'Drug Allergy', value: 'drug_allergies' },
  { label: 'Other Allergy', value: 'other_allergies' },
  { label: 'Lifestyle Habits', value: 'lifestyles' }
]

const PatientMedicalHistory: FC = (): ReactElement => {
  const {
    isMedicalHistory,
    patientMedicalHistory = [],
    isLoading,
    isSaving,
    savePatientMedicalHistory
  } = usePatientMedicalHistory()

  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm] = useDebouncedValue(searchTerm, 200)
  const [selectedValue, setSelectedValue] = useState<string | null>(null)

  const form = useForm({
    defaultValues: {
      isMedicalHistoryEnabled: isMedicalHistory ?? true,
      filterType: 'conditions',
      medicalHistory: patientMedicalHistory
    },
    onSubmit: async ({ value }) => {
      await savePatientMedicalHistory({
        medical_history_data: value.medicalHistory,
        is_medical_history: value.isMedicalHistoryEnabled
      })
      form.reset(value) // Reset dirty state
    }
  })

  const filterType = useStore(form.store, (state) => state.values.filterType)
  const isMedicalHistoryEnabled = useStore(
    form.store,
    (state) => state.values.isMedicalHistoryEnabled
  )
  const localMedicalHistory = useStore(
    form.store,
    (state) => state.values.medicalHistory
  )
  const isDirty = useStore(form.store, (meta) => meta.isDirty)

  const { medicalHistoryOptions, isFetching, isError } = useMedicalHistory({
    filterType,
    debouncedSearchTerm
  })

  // Keep local form state in sync when initial data changes
  useEffect(() => {
    if (!isLoading && !isEqual(patientMedicalHistory, localMedicalHistory)) {
      form.setFieldValue('medicalHistory', patientMedicalHistory)
    }
  }, [form, isLoading, localMedicalHistory, patientMedicalHistory])

  const handleSelect = (optionValue: string | null) => {
    if (!optionValue) return

    const selectedOption = medicalHistoryOptions.find(
      (option: MedicalHistory) => option.id === optionValue
    )

    if (
      selectedOption &&
      !localMedicalHistory.some(
        (item: MedicalHistory) => item.id === selectedOption.id
      )
    ) {
      form.setFieldValue('medicalHistory', [
        ...localMedicalHistory,
        selectedOption
      ])
    }

    setSearchTerm('')
    setSelectedValue(null)
  }

  const handleDelete = (id: string) => {
    form.setFieldValue(
      'medicalHistory',
      localMedicalHistory.filter((item: MedicalHistory) => item.id !== id)
    )
  }

  const options = useMemo(
    () =>
      medicalHistoryOptions.map((item: MedicalHistory) => ({
        value: item.id,
        label: item.name
      })),
    [medicalHistoryOptions]
  )

  return (
    <Card>
      <Card.Section py={'lg'}>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            form.handleSubmit()
          }}
        >
          <Stack gap={'lg'}>
            <Flex justify={'flex-end'}>
              {/* Enable/Disable Medical History Switch */}
              <form.Field name="isMedicalHistoryEnabled">
                {(field) => (
                  <Switch
                    checked={field.state.value}
                    fw={600}
                    label="Medical History Enabled"
                    labelPosition="left"
                    onChange={(e) =>
                      field.handleChange(e.currentTarget.checked)
                    }
                    withThumbIndicator={false}
                  />
                )}
              </form.Field>
            </Flex>

            {/* Filters for searching medical history types */}
            <form.Field name="filterType">
              {(field) => (
                <Radio.Group
                  label="Select Medical History type for precise results"
                  value={field.state.value}
                  onChange={field.handleChange}
                >
                  <Group mt="xs">
                    {MEDICAL_HISTORY_TYPES.map(({ label, value }) => (
                      <Radio
                        key={value}
                        disabled={!isMedicalHistoryEnabled}
                        label={label}
                        opacity={!isMedicalHistoryEnabled ? 0.5 : 1}
                        value={value}
                      />
                    ))}
                  </Group>
                </Radio.Group>
              )}
            </form.Field>

            <Select
              data={options}
              disabled={!isMedicalHistoryEnabled}
              leftSection={<MagnifyingGlassIcon />}
              nothingFoundMessage={
                isFetching ? 'Loading...' : 'No results found'
              }
              onSearchChange={
                !isMedicalHistoryEnabled ? undefined : setSearchTerm
              }
              onChange={handleSelect}
              placeholder="Select a parameter..."
              rightSection={
                isFetching && debouncedSearchTerm.trim().length > 1 ? (
                  <Loader size={18} />
                ) : (
                  <></>
                )
              }
              searchable={isMedicalHistoryEnabled}
              searchValue={searchTerm}
              value={selectedValue}
            />

            {isError && debouncedSearchTerm.trim().length > 1 && (
              <Alert
                icon={<WarningCircleIcon size={16} />}
                title="Error"
                color="red"
              >
                Failed to fetch search results
              </Alert>
            )}

            {isLoading ? (
              <Group gap={'xs'}>
                <Skeleton
                  h={30}
                  w={100}
                />
                <Skeleton
                  h={30}
                  w={100}
                />
                <Skeleton
                  h={30}
                  w={100}
                />
                <Skeleton
                  h={30}
                  w={100}
                />
              </Group>
            ) : (
              <Flex
                gap="xs"
                wrap="wrap"
              >
                {localMedicalHistory.length > 0 ? (
                  localMedicalHistory.map(({ id, name }) => (
                    <PatientMedicalHistoryItem
                      key={id}
                      id={id}
                      name={name}
                      disabled={!isMedicalHistoryEnabled}
                      onDelete={handleDelete}
                    />
                  ))
                ) : (
                  <Text c="dimmed">No medical history selected</Text>
                )}
              </Flex>
            )}
          </Stack>
          <Flex justify={'flex-end'}>
            <Button
              type="submit"
              disabled={!isDirty}
              loading={isSaving}
            >
              Save
            </Button>
          </Flex>
        </form>
      </Card.Section>
    </Card>
  )
}

export default PatientMedicalHistory
