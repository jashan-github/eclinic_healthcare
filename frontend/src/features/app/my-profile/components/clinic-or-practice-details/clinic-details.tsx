import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Grid, Stack, TextInput } from '@mantine/core'
import { DatePickerInput } from '@mantine/dates'
import { format } from 'date-fns'
import { type FC, type ReactElement } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'

const formSchema = z.object({
  clinic_name: z.string().min(2).max(50),
  phone_number: z.string().min(2).max(100),
  clinic_opened_on: z.string().min(2).max(500),
  address_line_1: z.string().min(2).max(100),
  address_line_2: z.string().min(2).max(100),
  state: z.string().min(2).max(100),
  country: z.string().min(2).max(100),
  city: z.string().min(2).max(100),
  pincode: z.string().min(2).max(100),
  location: z.string().min(2).max(100)
})

type FormData = z.infer<typeof formSchema>

const ClinicDetails: FC = (): ReactElement => {
  const {
    control,
    handleSubmit,
    formState: { errors }
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      clinic_name: '',
      phone_number: '',
      clinic_opened_on: '',
      address_line_1: '',
      address_line_2: '',
      state: '',
      country: '',
      city: '',
      pincode: '',
      location: ''
    }
  })

  const onSubmit = (data: FormData) => {
    console.log('Form submitted:', data)
    // Add API call or other logic here
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Stack my={'md'}>
        <Controller
          name="clinic_name"
          control={control}
          render={({ field }) => (
            <TextInput
              error={errors.clinic_name?.message}
              label="Clinic Name"
              placeholder="Enter the clinic name"
              {...field}
            />
          )}
        />

        <Controller
          name="phone_number"
          control={control}
          render={({ field }) => (
            <TextInput
              description="This number will be visible on your profile publicly!"
              error={errors.phone_number?.message}
              inputWrapperOrder={['label', 'input', 'description', 'error']}
              label="Phone Number"
              placeholder="Enter the clinic phone number"
              {...field}
            />
          )}
        />

        <Controller
          name="clinic_opened_on"
          control={control}
          render={({ field }) => (
            <DatePickerInput
              defaultValue={null}
              label="Pick date"
              placeholder="Pick date"
              value={field.value ? new Date(field.value) : null}
              onChange={(date) =>
                field.onChange(date ? format(date, 'yyyy-MM-dd') : '')
              }
              error={errors.clinic_opened_on?.message}
            />
          )}
        />

        <Controller
          name="address_line_1"
          control={control}
          render={({ field }) => (
            <TextInput
              label="Building/Apartment name"
              withAsterisk
              placeholder="Building/Apartment name"
              {...field}
              error={errors.address_line_1?.message}
            />
          )}
        />
        <Controller
          name="address_line_2"
          control={control}
          render={({ field }) => (
            <TextInput
              label="Street name"
              placeholder="Street name"
              {...field}
              error={errors.address_line_2?.message}
            />
          )}
        />
        <Grid>
          <Grid.Col span={6}>
            <Controller
              name="pincode"
              control={control}
              render={({ field }) => (
                <TextInput
                  label="Pincode"
                  placeholder="Pincode"
                  // disabled
                  {...field}
                  error={errors.pincode?.message}
                />
              )}
            />
          </Grid.Col>
          <Grid.Col span={6}>
            <Controller
              name="city"
              control={control}
              render={({ field }) => (
                <TextInput
                  label="City"
                  placeholder="City"
                  // disabled
                  {...field}
                  error={errors.city?.message}
                />
              )}
            />
          </Grid.Col>
        </Grid>
        <Controller
          name="state"
          control={control}
          render={({ field }) => (
            <TextInput
              label="State"
              placeholder="State"
              {...field}
              error={errors.state?.message}
            />
          )}
        />
        <Controller
          name="country"
          control={control}
          render={({ field }) => (
            <TextInput
              label="Country"
              placeholder="Country"
              {...field}
              error={errors.country?.message}
            />
          )}
        />

        <Controller
          name="location"
          control={control}
          render={({ field }) => (
            <TextInput
              label="Location"
              placeholder="Location"
              {...field}
              error={errors.location?.message}
            />
          )}
        />

        <Button
          type="submit"
          fullWidth
        >
          Save
        </Button>
      </Stack>
    </form>
  )
}

export default ClinicDetails
