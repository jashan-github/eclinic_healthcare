import BaseSideSheet from '@/components/orvo/base-side-sheet'
import {
  Button,
  Checkbox,
  Collapse,
  Group,
  Input,
  NumberInput,
  Radio,
  Select,
  Stack,
  Switch,
  Text,
  Combobox,
  InputBase,
  useCombobox
} from '@mantine/core'
import {
  CaretDownIcon,
  CaretUpIcon,
  MagnifyingGlassIcon
} from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'

// Duration dropdown options
const durationDropdownItems = [
  { label: '2 Minutes', value: '2' },
  { label: '3 Minutes', value: '3' },
  { label: '5 Minutes', value: '5' },
  { label: '7 Minutes', value: '7' },
  { label: '10 Minutes', value: '10' },
  { label: '15 Minutes', value: '15' },
  { label: '20 Minutes', value: '20' },
  { label: '25 Minutes', value: '25' },
  { label: '30 Minutes', value: '30' },
  { label: '35 Minutes', value: '35' },
  { label: '40 Minutes', value: '40' },
  { label: '45 Minutes', value: '45' },
  { label: '50 Minutes', value: '50' },
  { label: '55 Minutes', value: '55' },
  { label: '60 Minutes', value: '60' },
  { label: '65 Minutes', value: '65' },
  { label: '70 Minutes', value: '70' },
  { label: '75 Minutes', value: '75' },
  { label: '80 Minutes', value: '80' },
  { label: '85 Minutes', value: '85' },
  { label: '90 Minutes', value: '90' },
  { label: '2 hours', value: '120' },
  { label: '3 hours', value: '180' },
  { label: '4 hours', value: '240' },
  { label: '5 hours', value: '300' },
  { label: '6 hours', value: '360' }
]

const followupValidityDropdownOptions = [
  { label: '1 day from initial consultation', value: '1' },
  { label: '2 days from initial consultation', value: '2' },
  { label: '3 days from initial consultation', value: '3' },
  { label: '4 days from initial consultation', value: '4' },
  { label: '5 days from initial consultation', value: '5' },
  { label: '6 days from initial consultation', value: '6' },
  { label: '7 days from initial consultation', value: '7' },
  { label: '8 days from initial consultation', value: '8' },
  { label: '9 days from initial consultation', value: '9' },
  { label: '10 days from initial consultation', value: '10' },
  { label: '11 days from initial consultation', value: '11' },
  { label: '12 days from initial consultation', value: '12' },
  { label: '13 days from initial consultation', value: '13' },
  { label: '14 days from initial consultation', value: '14' },
  { label: '15 days from initial consultation', value: '15' },
  { label: '16 days from initial consultation', value: '16' },
  { label: '17 days from initial consultation', value: '17' },
  { label: '18 days from initial consultation', value: '18' },
  { label: '19 days from initial consultation', value: '19' },
  { label: '20 days from initial consultation', value: '20' },
  { label: '21 days from initial consultation', value: '21' },
  { label: '22 days from initial consultation', value: '22' },
  { label: '23 days from initial consultation', value: '23' },
  { label: '24 days from initial consultation', value: '24' },
  { label: '25 days from initial consultation', value: '25' },
  { label: '26 days from initial consultation', value: '26' },
  { label: '27 days from initial consultation', value: '27' },
  { label: '28 days from initial consultation', value: '28' },
  { label: '29 days from initial consultation', value: '29' },
  { label: '30 days from initial consultation', value: '30' },
  { label: '31 days from initial consultation', value: '31' }
]

// Zod schema for form validation
const serviceSchema = z.object({
  serviceName: z.string().min(1, 'Service name is required'),
  serviceMode: z.enum(['in-clinic', 'video']),
  paymentSettings: z.enum(['pre-paid', 'post-consultation']),
  price: z.string().optional(),
  skipPrice: z.boolean(),
  duration: z.string().min(1, 'Duration is required'),
  followup_validity: z.string().min(1, 'Duration is required').optional(),
  nickname: z.string().optional(),
  allowBooking: z.boolean(),
  advanceBookingDays: z
    .number()
    .min(0, 'Advance booking days cannot be negative')
    .optional(),
  minimumNoticeHours: z
    .number()
    .min(0, 'Minimum notice hours cannot be negative')
    .optional(),
  appointmentType: z.enum(['regular', 'followup']).optional()
})

type ServiceFormData = z.infer<typeof serviceSchema>

interface CreateNewServiceProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
}

const CreateNewService: FC<CreateNewServiceProps> = ({
  isOpen,
  setIsOpen
}): ReactElement => {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption()
  })

  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)
  const [data, setData] = useState<string[]>([
    'Consultation',
    'Therapy',
    'Check-up'
  ])
  const [search, setSearch] = useState('')

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<ServiceFormData>({
    resolver: zodResolver(serviceSchema),
    defaultValues: {
      serviceName: '',
      serviceMode: 'in-clinic',
      paymentSettings: 'pre-paid',
      followup_validity: '7',
      price: '',
      skipPrice: false,
      duration: '',
      nickname: '',
      allowBooking: true,
      advanceBookingDays: 0,
      minimumNoticeHours: 0,
      appointmentType: 'regular'
    }
  })

  const skipPrice = watch('skipPrice')
  const appointmentType = watch('appointmentType')
  const advanceBookingDays = watch('advanceBookingDays')
  const minimumNoticeHours = watch('minimumNoticeHours')

  const exactOptionMatch = data.some((item) => item === search)
  const filteredOptions = exactOptionMatch
    ? data
    : data.filter((item) =>
      item.toLowerCase().includes(search.toLowerCase().trim())
    )

  const options = filteredOptions.map((item) => (
    <Combobox.Option
      value={item}
      key={item}
    >
      {item}
    </Combobox.Option>
  ))

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const onSubmit = (formData: ServiceFormData) => {
    // TODO: Replace with backend API call to create service
    setIsOpen(false)
  }

  return (
    <BaseSideSheet
      size="lg"
      title="Create New Service"
      isOpen={isOpen}
      onOpenChange={setIsOpen}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack gap="lg">
          {/* Service Name Combobox */}
          <Controller
            name="serviceName"
            control={control}
            render={({ field }) => (
              <Combobox
                store={combobox}
                withinPortal={false}
                onOptionSubmit={(val) => {
                  if (val === '$create') {
                    setData((current) => [...current, search])
                    setValue('serviceName', search)
                    setSearch(search)
                  } else {
                    setValue('serviceName', val)
                    setSearch(val)
                  }
                  combobox.closeDropdown()
                }}
              >
                <Combobox.Target>
                  <InputBase
                    leftSection={<MagnifyingGlassIcon size={20} />}
                    value={search}
                    onChange={(event) => {
                      combobox.openDropdown()
                      combobox.updateSelectedOptionIndex()
                      setSearch(event.currentTarget.value)
                    }}
                    onClick={() => combobox.openDropdown()}
                    onFocus={() => combobox.openDropdown()}
                    onBlur={() => {
                      combobox.closeDropdown()
                      setSearch(field.value || '')
                    }}
                    placeholder="Start typing a service"
                    error={errors.serviceName?.message}
                  />
                </Combobox.Target>
                <Combobox.Dropdown>
                  <Combobox.Options>
                    {options}
                    {!exactOptionMatch && search.trim().length > 0 && (
                      <Combobox.Option value="$create">
                        + Create {search}
                      </Combobox.Option>
                    )}
                  </Combobox.Options>
                </Combobox.Dropdown>
              </Combobox>
            )}
          />

          {/* Service Mode */}
          <Stack gap="sm">
            <Text fw={600}>Service Mode</Text>
            <Controller
              name="serviceMode"
              control={control}
              render={({ field }) => (
                <Radio.Group
                  {...field}
                  name="serviceMode"
                  onChange={field.onChange}
                >
                  <Group gap="md">
                    <Radio
                      value="in-clinic"
                      label="In-Clinic"
                    />
                    <Radio
                      value="video"
                      label="Video"
                    />
                  </Group>
                </Radio.Group>
              )}
            />
          </Stack>

          {/* Payment Settings */}
          <Stack gap="sm">
            <Text fw={600}>Payment Settings</Text>
            <Controller
              name="paymentSettings"
              control={control}
              render={({ field }) => (
                <Radio.Group
                  {...field}
                  name="paymentSettings"
                  onChange={field.onChange}
                >
                  <Group gap="md">
                    <Radio
                      value="pre-paid"
                      label="Pre-paid"
                    />
                    <Radio
                      value="post-consultation"
                      label="Post Consultation"
                    />
                  </Group>
                </Radio.Group>
              )}
            />
          </Stack>

          {/* Price Input */}
          <Stack gap="sm">
            <Text fw={600}>Price</Text>
            <Input.Wrapper error={errors.price?.message}>
              <Controller
                name="price"
                control={control}
                render={({ field }) => (
                  <Input
                    {...field}
                    leftSection="XCG"
                    leftSectionWidth={55}
                    leftSectionProps={{
                      style: {
                        paddingRight: '10px',
                        color: '#495057',
                      },
                    }}
                    placeholder="200"
                    style={{ maxWidth: '50%' }}
                    disabled={skipPrice}
                    styles={{
                      input: {
                        paddingLeft: '65px !important',
                      },
                    }}
                  />
                )}
              />
            </Input.Wrapper>
            <Controller
              name="skipPrice"
              control={control}
              render={({ field }) => (
                <Checkbox
                  label="I prefer not to define the price now"
                  checked={field.value}
                  onChange={(e) => {
                    field.onChange(e.currentTarget.checked)
                    if (e.currentTarget.checked) setValue('price', '')
                  }}
                />
              )}
            />
          </Stack>

          {/* Duration */}
          <Stack gap="sm">
            <Text fw={600}>Duration</Text>
            <Controller
              name="duration"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  placeholder="Select duration"
                  data={durationDropdownItems}
                  style={{ maxWidth: '50%' }}
                  maxDropdownHeight={400}
                  error={errors.duration?.message}
                  onChange={field.onChange}
                />
              )}
            />
          </Stack>

          {/* Advanced Settings */}
          <Stack gap="sm">
            <Group
              justify="space-between"
              align="center"
            >
              <Stack gap={2}>
                <Text
                  fw={600}
                  size="sm"
                >
                  Advanced Settings
                </Text>
                <Text
                  size="xs"
                  c="dimmed"
                >
                  Set booking access & advance booking details
                </Text>
              </Stack>
              <Button
                variant="subtle"
                onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                rightSection={
                  isAdvancedOpen ? <CaretUpIcon /> : <CaretDownIcon />
                }
              >
                {isAdvancedOpen ? 'Hide' : 'Show'}
              </Button>
            </Group>
            <Collapse in={isAdvancedOpen}>
              <Stack gap="lg">
                {/* Nickname */}
                <Input.Wrapper
                  label="Set Nickname"
                  error={errors.nickname?.message}
                >
                  <Controller
                    name="nickname"
                    control={control}
                    render={({ field }) => (
                      <Input
                        {...field}
                        style={{ maxWidth: '50%' }}
                      />
                    )}
                  />
                </Input.Wrapper>

                {/* Allow Booking */}
                <Group
                  justify="space-between"
                  align="center"
                >
                  <Text size="sm">
                    Allow this service to be booked by patients?
                  </Text>
                  <Controller
                    name="allowBooking"
                    control={control}
                    render={({ field }) => (
                      <Switch
                        checked={field.value}
                        onChange={(e) =>
                          field.onChange(e.currentTarget.checked)
                        }
                      />
                    )}
                  />
                </Group>

                {/* Advance Booking */}
                <Input.Wrapper
                  label="Set advance booking of this service (in Days)"
                  description={`This booking can be booked ${advanceBookingDays || 0} days in advance by patients/staff`}
                  error={errors.advanceBookingDays?.message}
                >
                  <Controller
                    name="advanceBookingDays"
                    control={control}
                    render={({ field }) => (
                      <NumberInput
                        {...field}
                        hideControls
                        max={365}
                        maxLength={3}
                        rightSection="days"
                        rightSectionWidth={60}
                        mt={'sm'}
                        w={'50%'}
                      />
                    )}
                  />
                </Input.Wrapper>

                {/* Minimum Notice */}
                <Input.Wrapper
                  label="Minimum Notice"
                  description={`Appointments can only be booked before ${minimumNoticeHours || 0} hours in advance by patients`}
                  error={errors.minimumNoticeHours?.message}
                >
                  <Controller
                    name="minimumNoticeHours"
                    control={control}
                    render={({ field }) => (
                      <NumberInput
                        {...field}
                        hideControls
                        min={0}
                        max={365}
                        maxLength={3}
                        rightSection="hours"
                        rightSectionWidth={60}
                        mt={'sm'}
                        w={'50%'}
                      />
                    )}
                  />
                </Input.Wrapper>

                {/* Appointment Type */}
                <Stack gap="sm">
                  <Text fw={600}>Select Appointment Type</Text>
                  <Controller
                    name="appointmentType"
                    control={control}
                    render={({ field }) => (
                      <Radio.Group
                        {...field}
                        name="appointmentType"
                        onChange={field.onChange}
                      >
                        <Group gap="md">
                          <Radio
                            value="regular"
                            label="Regular"
                          />
                          <Radio
                            value="followup"
                            label="Followup"
                          />
                        </Group>
                      </Radio.Group>
                    )}
                  />
                </Stack>

                {/* Follow-up Validity */}
                {appointmentType === 'followup' && (
                  <Stack gap="sm">
                    <Text fw={600}>Follow-up Validity</Text>
                    <Controller
                      name="followup_validity"
                      control={control}
                      render={({ field }) => (
                        <Select
                          {...field}
                          placeholder="Select consultation validity"
                          data={followupValidityDropdownOptions}
                          style={{ maxWidth: '50%' }}
                          maxDropdownHeight={400}
                          error={errors.followup_validity?.message}
                          onChange={field.onChange}
                        />
                      )}
                    />
                  </Stack>
                )}
              </Stack>
            </Collapse>
          </Stack>

          {/* Create Service Button */}
          <Group mt={'xl'}>
            <Button
              type="submit"
              fullWidth
            >
              Create Service
            </Button>
          </Group>
        </Stack>
      </form>
    </BaseSideSheet>
  )
}

export default CreateNewService
