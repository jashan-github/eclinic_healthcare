import GlobalLoader from '@/components/orvo/common/global-loader'
import { useMedicalCouncils } from '@/hooks/use-medical-councils'
import type { Registration } from '@/types/registration'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { Button, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useRegistrations } from '../../../hooks/use-registrations'
import { useRegistrationStore } from '../../../stores/use-registration-store'

const formSchema = z.object({
  id: z.string().optional(),
  registration_number: z.string().min(2).max(100),
  // UI is a Select bound to medical-council UUIDs; enforce that shape here so
  // free-text or empty values can't reach the backend.
  registration_council: z.uuid('Please select a valid council'),
  registration_year: z
    .string()
    .regex(/^\d{4}$/, 'Select a valid year')
    .refine(
      (v) => parseInt(v, 10) <= new Date().getFullYear(),
      'Year cannot be in the future'
    )
})

const RegistrationForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, saveRegistration, updateRegistration } =
    useRegistrations()
  const { registration, processCancel, setRegistration } =
    useRegistrationStore()
  const { medicalCouncils, isLoadingMedicalCouncils } = useMedicalCouncils()

  const registrationForm = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      id: registration?.id || '',
      registration_number: registration?.registration_number || '',
      registration_council: registration?.registration_council || '',
      registration_year: registration?.registration_year || ''
    }
  })

  const handleAddRegistration = (data: Registration) => {
    saveRegistration(data, {
      onSuccess: () => {
        setRegistration(null)
        toast.success('Registration added successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to add registration: ${error.message}`)
      }
    })
  }

  const handleEditRegistration = (data: Registration) => {
    const registrationId = registrationForm.values.id
    if (!registrationId) return

    updateRegistration(
      { registrationId, data },
      {
        onSuccess: () => {
          setRegistration(null)
          toast.success('Registration updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update registration: ${error.message}`)
        }
      }
    )
  }

  if (isLoadingMedicalCouncils) return <GlobalLoader />

  return (
    <form
      onSubmit={registrationForm.onSubmit(
        registrationForm.values.id
          ? handleEditRegistration
          : handleAddRegistration
      )}
      className="space-y-8 px-1"
    >
      <TextInput
        label="Registration ID"
        placeholder="Enter Registration ID"
        classNames={{ input: 'orvo-base-input' }}
        {...registrationForm.getInputProps('registration_number')}
      />

      <Select
        label="Registration Council"
        placeholder="Select Council"
        data={medicalCouncils?.map(({ id, name, state }) => ({
          value: id,
          label: `${name} (${state})`
        }))}
        classNames={{ input: 'orvo-base-input' }}
        styles={{
          dropdown: {
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid #e5e7eb'
          }
        }}
        {...registrationForm.getInputProps('registration_council')}
      />

      <Select
        label="Valid From"
        placeholder="Select Year"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        {...registrationForm.getInputProps('registration_year')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          Save
        </Button>
        <Button
          className="flex grow"
          disabled={isSaving || isUpdating}
          color="red"
          type="button"
          onClick={processCancel}
        >
          Cancel
        </Button>
      </div>

      {registrationForm.errors.root && (
        <div className="text-red-500">{registrationForm.errors.root}</div>
      )}
    </form>
  )
}

export default RegistrationForm
