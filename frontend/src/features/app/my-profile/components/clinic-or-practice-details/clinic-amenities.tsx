import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { Button, Checkbox, Group, Stack, Text } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { useEffect, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useClinicAmenities } from '../../hooks/use-clinic-amenities'

const AmenitySchema = z.object({
  id: z.string(),
  name: z.string(),
  is_checked: z.boolean()
})

const ClinicAmenitiesFormSchema = z.object({
  id: z.string(),
  name: z.string(),
  amenities: z.array(AmenitySchema)
})

const formSchema = z.object({
  categories: z.array(ClinicAmenitiesFormSchema)
})

type FormValues = z.infer<typeof formSchema>

const ClinicAmenities = (): ReactElement => {
  const { amenities, isLoading, isSaving, error, saveAmenities } =
    useClinicAmenities()

  const clinicAmenitiesForm = useForm<FormValues>({
    validate: zodResolver(formSchema),
    initialValues: { categories: amenities || [] }
  })

  const submitClinicAmenities = (values: FormValues) => {
    saveAmenities(values.categories, {
      onSuccess: () => {
        toast.success('Your information has been updated successfully.')
        clinicAmenitiesForm.setValues({ categories: values.categories })
        clinicAmenitiesForm.resetDirty()
      },
      onError: (error: Error) => {
        toast.error('Failed to update information. Please try again.')
        console.error('Save failed:', error)
      }
    })
  }

  useEffect(() => {
    if (amenities) {
      clinicAmenitiesForm.setValues({ categories: amenities })
      clinicAmenitiesForm.resetDirty()
    }
  }, [amenities])

  if (isLoading || isSaving) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <form
      onSubmit={clinicAmenitiesForm.onSubmit(submitClinicAmenities)}
      className="space-y-8 py-4 pb-20"
    >
      {clinicAmenitiesForm.values.categories?.map((amenityCategory, index) => (
        <Stack
          key={amenityCategory.id}
          gap="xs"
        >
          <Text
            fw={600}
            size="lg"
            className="capitalize"
          >
            {amenityCategory.name}
          </Text>
          <Group className="border bg-white border-gray-300 rounded p-4">
            {amenityCategory.amenities.map(({ id, name }, itemIndex) => (
              <Group
                key={id}
                className="w-full"
              >
                <Text
                  size="sm"
                  className="capitalize"
                >
                  {name}
                </Text>
                <Checkbox
                  checked={
                    clinicAmenitiesForm.getInputProps(
                      `categories.${index}.amenities.${itemIndex}.is_checked`
                    ).value ?? false
                  }
                  onChange={(event) =>
                    clinicAmenitiesForm.setFieldValue(
                      `categories.${index}.amenities.${itemIndex}.is_checked`,
                      event.currentTarget.checked
                    )
                  }
                />
              </Group>
            ))}
            {clinicAmenitiesForm.errors[`categories.${index}.amenities`] && (
              <Text
                color="red"
                size="sm"
              >
                {clinicAmenitiesForm.errors[`categories.${index}.amenities`]}
              </Text>
            )}
          </Group>
        </Stack>
      ))}

      <Button
        type="submit"
        variant="outline"
        className="w-full"
        loading={isSaving}
        aria-label={isSaving ? 'Saving' : 'Save'}
      >
        Save
      </Button>
    </form>
  )
}

export default ClinicAmenities
