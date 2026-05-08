import { useEffect, useState } from 'react'
import CustomFieldLabel from '@/components/orvo/custom-field-label'
import {
  ThreeStateButton,
  type ThreeStateButtonValue
} from '@/components/orvo/three-state-button'
import {
  ActionIcon,
  Button,
  Checkbox,
  Flex,
  Grid,
  Group,
  Radio,
  Select,
  Skeleton,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core'
import { GearSixIcon, PhoneIcon } from '@phosphor-icons/react'
import { useMemo, type FC, type ReactElement } from 'react'
import { usePatientFields } from '../../hooks/use-patient-fields'
import { usePatientMedicalHistory } from '../../hooks/use-patient-medical-history'
import { useNewPatientForm } from '../../hooks/use-new-patient-form'
import { countryCodes } from '@/lib/country-codes'

interface NewPatientFormProps {
  openConfigureModal: (val: boolean) => void
}

const NewPatientForm: FC<NewPatientFormProps> = ({
  openConfigureModal
}): ReactElement => {
  const { isLoading: selectedPatientFieldsLoading, selectedPatientFields } =
    usePatientFields()
  const { isMedicalHistory, patientMedicalHistory } = usePatientMedicalHistory()
  const {
    form,
    noKnownMedicalHistory,
    setNoKnownMedicalHistory,
    isGeneratingUHID,
    generateUHIDForPatient,
    SALUTATIONS
  } = useNewPatientForm({ isMedicalHistory })

  // State to track medical history as an array of objects with optional notes
  const [medicalHistoryState, setMedicalHistoryState] = useState<
    {
      name: string
      value: ThreeStateButtonValue<{
        positive: 'Yes'
        negative: 'No'
        indeterminate: 'NA'
      }>
      notes?: string
    }[]
  >([])

  useEffect(() => {
    // Check if the fetched data is available (not empty)
    // AND if the local state has not been initialized yet (is empty)
    if (patientMedicalHistory.length > 0 && medicalHistoryState.length === 0) {
      setMedicalHistoryState(
        patientMedicalHistory.map(({ name }) => ({
          name,
          value: 'NA'
        }))
      )
    }
  }, [patientMedicalHistory, medicalHistoryState.length]) // Dependency on fetched data

  // Update medical history state on value change
  const handleMedicalHistoryChange = (
    name: string,
    value: ThreeStateButtonValue<{
      positive: 'Yes'
      negative: 'No'
      indeterminate: 'NA'
    }>
  ) => {
    setMedicalHistoryState((prev) =>
      prev.map((item) =>
        item.name === name
          ? {
              ...item,
              value,
              notes: value === 'Yes' ? item.notes || '' : undefined
            }
          : item
      )
    )
  }

  // Update notes for a specific medical history field
  const handleNotesChange = (name: string, notes: string) => {
    setMedicalHistoryState((prev) =>
      prev.map((item) => (item.name === name ? { ...item, notes } : item))
    )
  }

  // Handle form submission
  const handleSubmit = async (values: typeof form.state.values) => {
    const payload = {
      ...values,
      medicalHistory: noKnownMedicalHistory ? [] : medicalHistoryState
    }
    try {
      await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } catch (error) {
      console.error('Error submitting patient data:', error)
    }
  }

  const showSalutation = useMemo(() => {
    return selectedPatientFields.some((f) => f.name === 'salutation')
  }, [selectedPatientFields])

  return (
    <form onSubmit={() => form.handleSubmit(handleSubmit)}>
      <Stack gap={'md'}>
        <Title order={4}>Basic Information</Title>

        {/* Patient Phone number */}
        <Stack gap={2}>
          <CustomFieldLabel label="Phone Number" />
          <Grid gutter={'md'}>
            <Grid.Col span={2}>
              <form.Field name="country_code">
                {({ state, handleChange }) => (
                  <Select
                    value={state.value}
                    onChange={(value) => handleChange(value || '91')}
                    data={countryCodes.map((c) => ({
                      value: c.value,
                      label: c.label
                    }))}
                    searchable
                    nothingFoundMessage="No country found"
                    error={state.meta.errors.join(', ')}
                    withAsterisk
                  />
                )}
              </form.Field>
            </Grid.Col>
            <Grid.Col span={3}>
              <form.Field name="phone">
                {({ state, handleChange }) => (
                  <TextInput
                    value={state.value}
                    onChange={(e) => handleChange(e.target.value)}
                    error={state.meta.errors.join(', ')}
                    placeholder="Enter your phone number"
                    rightSection={<PhoneIcon weight={'fill'} />}
                    withAsterisk
                  />
                )}
              </form.Field>
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Patient Name */}
        <Stack gap={1}>
          <CustomFieldLabel label="Patient Name" />
          <Grid>
            {showSalutation && (
              <Grid.Col span={1}>
                <form.Field name="salutation">
                  {({ state, handleChange }) => (
                    <Select
                      data={SALUTATIONS}
                      value={state.value}
                      onChange={(value) =>
                        handleChange(
                          value as 'Mr' | 'Ms' | 'Mrs' | 'Dr' | 'Other'
                        )
                      }
                      error={state.meta.errors.join(', ')}
                      withAsterisk
                    />
                  )}
                </form.Field>
              </Grid.Col>
            )}
            <Grid.Col span={2}>
              <form.Field name="first_name">
                {({ state, handleChange }) => (
                  <TextInput
                    value={state.value}
                    onChange={(e) => handleChange(e.target.value)}
                    error={state.meta.errors.join(', ')}
                    placeholder="First name"
                    withAsterisk
                  />
                )}
              </form.Field>
            </Grid.Col>
            <Grid.Col span={2}>
              <form.Field name="last_name">
                {({ state, handleChange }) => (
                  <TextInput
                    value={state.value}
                    onChange={(e) => handleChange(e.target.value)}
                    error={state.meta.errors.join(', ')}
                    placeholder="Last name"
                  />
                )}
              </form.Field>
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Patient Age/DOB */}
        <Grid align={'self-end'}>
          <Grid.Col span={2}>
            <form.Field name="age">
              {({ state, handleChange }) => (
                <TextInput
                  label="Age (in Years)"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  error={state.meta.errors.join(', ')}
                />
              )}
            </form.Field>
          </Grid.Col>
          <Grid.Col span={2}>
            <form.Field name="dob">
              {({ state, handleChange }) => (
                <TextInput
                  label="Date of Birth"
                  type="date"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  error={state.meta.errors.join(', ')}
                />
              )}
            </form.Field>
          </Grid.Col>
        </Grid>

        {/* Gender */}
        <Grid>
          <Grid.Col span={4}>
            <form.Field name="gender">
              {({ state, handleChange }) => (
                <Radio.Group
                  label="Gender"
                  value={state.value}
                  onChange={(value) =>
                    handleChange(value as 'male' | 'female' | 'other')
                  }
                  error={state.meta.errors.join(', ')}
                  withAsterisk
                >
                  <Group>
                    <Radio
                      value="male"
                      label="Male"
                    />
                    <Radio
                      value="female"
                      label="Female"
                    />
                    <Radio
                      value="other"
                      label="Other"
                    />
                  </Group>
                </Radio.Group>
              )}
            </form.Field>
          </Grid.Col>
        </Grid>

        <Stack gap={2}>
          <CustomFieldLabel label="UHID" />
          <Grid>
            <Grid.Col span={2}>
              <form.Field name="uhid">
                {({ state, handleChange }) => (
                  <TextInput
                    value={state.value}
                    onChange={(e) => handleChange(e.target.value)}
                    error={state.meta.errors.join(', ')}
                    withAsterisk
                  />
                )}
              </form.Field>
            </Grid.Col>
            <Grid.Col span={2}>
              <Button
                fullWidth
                loading={isGeneratingUHID}
                variant={'outline'}
                onClick={generateUHIDForPatient}
              >
                Generate UHID
              </Button>
            </Grid.Col>
          </Grid>
        </Stack>

        {/* Medical History Section */}
        <Grid>
          <Grid.Col span={12}>
            <Flex
              align={'center'}
              justify={'flex-start'}
              gap={'md'}
              className="pt-lg"
            >
              <Title order={4}>Patient Medical History</Title>
              <Checkbox
                checked={noKnownMedicalHistory}
                label="No known medical history"
                onChange={() => setNoKnownMedicalHistory((prev) => !prev)}
              />
            </Flex>
          </Grid.Col>
          {patientMedicalHistory &&
            !noKnownMedicalHistory &&
            patientMedicalHistory.map(({ name }) => (
              <Grid.Col
                key={name}
                span={4}
              >
                <Flex
                  align="center"
                  justify={'flex-start'}
                  gap="xs"
                >
                  <ThreeStateButton
                    label={name}
                    initialValue={
                      medicalHistoryState.find((item) => item.name === name)
                        ?.value || 'NA'
                    }
                    positive="Yes"
                    negative="No"
                    indeterminate="NA"
                    onValueChange={(value) =>
                      handleMedicalHistoryChange(name, value)
                    }
                  />
                  {medicalHistoryState.find((item) => item.name === name)
                    ?.value === 'Yes' && (
                    <TextInput
                      placeholder="Since/Frequency"
                      value={
                        medicalHistoryState.find((item) => item.name === name)
                          ?.notes || ''
                      }
                      onChange={(e) => handleNotesChange(name, e.target.value)}
                      size="sm"
                    />
                  )}
                </Flex>
              </Grid.Col>
            ))}
          <Grid.Col span={4}>
            <Flex
              align={'center'}
              gap={'xs'}
            >
              <ActionIcon
                onClick={() => openConfigureModal(true)}
                radius={'xl'}
                size={'xl'}
                variant={'outline'}
              >
                <GearSixIcon weight={'fill'} />
              </ActionIcon>
              <Text
                fw={600}
                size={'sm'}
              >
                Configure
              </Text>
            </Flex>
          </Grid.Col>
        </Grid>

        {/* Additional Information */}
        {selectedPatientFieldsLoading ? (
          <Stack gap={'sm'}>
            <Skeleton h={30} />
            <Skeleton h={30} />
            <Skeleton h={30} />
          </Stack>
        ) : (
          <>
            {selectedPatientFields.length > 0 && (
              <Title
                pt={'md'}
                order={4}
              >
                Additional Information
              </Title>
            )}
            {selectedPatientFields.map(({ name, label }) => (
              <Grid key={name}>
                <Grid.Col span={2}>
                  <form.Field name={name}>
                    {({ state, handleChange }) => (
                      <TextInput
                        label={label}
                        value={state.value}
                        onChange={(e) => handleChange(e.target.value)}
                        error={state.meta.errors.join(', ')}
                      />
                    )}
                  </form.Field>
                </Grid.Col>
              </Grid>
            ))}
          </>
        )}

        <Flex justify={'flex-end'}>
          <Button type="submit">Add Patient</Button>
        </Flex>
      </Stack>
    </form>
  )
}

export default NewPatientForm
