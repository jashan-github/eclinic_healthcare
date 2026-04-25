import {
  Button,
  Radio,
  Select,
  TextInput,
  Group,
  Stack,
  Text
} from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import { useForm } from '@mantine/form'
import { z } from 'zod'
import { zodResolver } from 'mantine-form-zod-resolver'

const formSchema = z.object({
  salutation: z.enum(['Mr', 'Ms', 'Dr'], {
    error: () => 'Salutation is required'
  }),
  firstName: z.string().min(1, 'First name is required'),
  middleName: z.string().optional(),
  lastName: z.string().min(1, 'Last name is required'),
  gender: z.enum(['male', 'female', 'other'], {
    error: () => 'Gender is required'
  }),
  dob: z.string().min(1, 'Date of birth is required'),
  countryCode: z.string().min(1, 'Country code is required'),
  mobile: z.string().min(10, 'Mobile number must be at least 10 digits'),
  email: z.email('Invalid email address')
})

const CreateWorkspaceForm: FC = (): ReactElement => {
  const form = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      salutation: 'Mr',
      firstName: '',
      middleName: '',
      lastName: '',
      gender: 'male',
      dob: '',
      countryCode: '+91',
      mobile: '',
      email: ''
    }
  })

  const onSubmit = (data: z.infer<typeof formSchema>) => {
    console.log('Form submitted:', data)
  }

  return (
    <form
      onSubmit={form.onSubmit(onSubmit)}
      className="space-y-4"
    >
      <Stack gap="sm">
        <Text>Your Name</Text>
        <Group
          wrap="nowrap"
          gap="md"
          grow
        >
          <Select
            label="Salutation"
            placeholder="Select salutation"
            data={['Mr', 'Ms', 'Dr']}
            {...form.getInputProps('salutation')}
          />
          <Group grow>
            <TextInput
              placeholder="First name"
              {...form.getInputProps('firstName')}
            />
            <TextInput
              placeholder="Middle name (Optional)"
              {...form.getInputProps('middleName')}
            />
            <TextInput
              placeholder="Last name"
              {...form.getInputProps('lastName')}
            />
          </Group>
        </Group>

        <Stack gap="xs">
          <Text>Gender</Text>
          <Radio.Group {...form.getInputProps('gender')}>
            <Group gap="md">
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
          {form.errors.gender && (
            <Text
              size="xs"
              color="red"
            >
              {form.errors.gender}
            </Text>
          )}
        </Stack>

        <Stack gap="xs">
          <Text>Date of Birth</Text>
          <TextInput
            type="date"
            {...form.getInputProps('dob')}
          />
        </Stack>

        <Stack gap="xs">
          <Text>Mobile number with country code</Text>
          <Group
            wrap="nowrap"
            gap="md"
          >
            <Select
              label="Country Code"
              placeholder="Select code"
              data={['+1', '+44', '+91']}
              disabled
              {...form.getInputProps('countryCode')}
              style={{ width: '100px' }}
            />
            <TextInput
              type="tel"
              placeholder="Mobile number"
              {...form.getInputProps('mobile')}
            />
          </Group>
        </Stack>

        <Stack gap="xs">
          <Text>Email Address</Text>
          <TextInput
            type="email"
            placeholder="Email address"
            {...form.getInputProps('email')}
          />
        </Stack>

        <Button type="submit">Next</Button>
      </Stack>
    </form>
  )
}

export default CreateWorkspaceForm
