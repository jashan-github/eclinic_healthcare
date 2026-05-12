import BaseSideSheet from '@/components/orvo/base-side-sheet'
import {
  Button,
  Collapse,
  Group,
  Input,
  NumberInput,
  Radio,
  Select,
  Stack,
  Switch,
  Text,
  useCombobox
} from '@mantine/core'
import {
  CaretDownIcon,
  CaretUpIcon,
} from '@phosphor-icons/react'
import { useState, type FC, type ReactElement } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCalendarService } from '@/features/app/calendar/hooks/use-calendar-service'
import { useCreateAdminService, useUpdateAdminService } from '@/hooks/use-admin-service-hooks'
import type { CreateAdminServicePayload } from '@/services/admin-service'
import { useAuth } from '@/context/auth/auth-context-utils'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useEffect } from 'react'
import { toast } from 'react-toastify'
import { getCalendarServices as getAvailableDoctorServices } from '@/features/app/calendar/services/calendar-services-service-doctor'
import { addDoctorService, createDoctorServicePricing } from '@/services/weekly-schedule'

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
  type: z.enum(['in-clinic', 'video']),
  paymentSettings: z.enum(['pre-paid', 'post-consultation']),
  price: z
    .string()
    .optional()
    .refine(
      (v) => !v || (/^\d+(\.\d{1,2})?$/.test(v) && parseFloat(v) > 0),
      'Price must be a positive number with up to 2 decimal places'
    ),
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
  serviceId?: string // Optional: if provided, component is in update mode
}

const CreateNewService: FC<CreateNewServiceProps> = ({
  isOpen,
  setIsOpen,
  serviceId
}): ReactElement => {
  const isUpdateMode = !!serviceId
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption()
  })

  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)

  const { user } = useAuth()
  const roleFromStorage = localStorage.getItem('role')
  const userRole = (user?.role || roleFromStorage || 'doctor').toLowerCase()
  const isAdmin = userRole === 'super_admin' || userRole === 'clinic_admin'
  const queryClient = useQueryClient()

  const { calendarServices } = useCalendarService(isAdmin)
  const createAdminServiceMutation = useCreateAdminService()
  const updateAdminServiceMutation = useUpdateAdminService()

  const { data: availableDoctorServices = [] } = useQuery({
    queryKey: ['doctor-services-available'],
    queryFn: getAvailableDoctorServices,
    enabled: !isAdmin && isOpen && !isUpdateMode,
  })

  const createDoctorServiceMutation = useMutation({
    mutationFn: async (data: ServiceFormData) => {
      const serviceId = data.serviceName
      const slotDuration = Number(data.duration) || 30
      const priceAmount = Number(data.price || 0)

      const response = await addDoctorService({
        service_id: serviceId,
        slot_duration_minutes: slotDuration,
      })

      const assignmentId = response.data?.id
      if (assignmentId && slotDuration !== 30) {
        await api.patch(`/v1/doctor/services/${assignmentId}`, {
          slot_duration_minutes: slotDuration,
        })
      }

      if (priceAmount > 0) {
        await createDoctorServicePricing({
          service_id: serviceId,
          price_amount: priceAmount,
          currency: 'XCG',
        })
      }

      return response
    },
    onSuccess: () => {
      toast.success('Service created successfully!')
      setIsOpen(false)
      queryClient.invalidateQueries({ queryKey: ['doctor-services'] })
      queryClient.invalidateQueries({ queryKey: ['doctor-services-available'] })
      queryClient.invalidateQueries({ queryKey: ['calendarServices'] })
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Unable to create service')
    },
  })

  const {
    control,
    handleSubmit,
    watch,
    reset,
    formState: { errors }
  } = useForm<ServiceFormData>({
    resolver: zodResolver(serviceSchema),
    defaultValues: {
      serviceName: '',
      type: 'in-clinic',
      paymentSettings: 'pre-paid',
      followup_validity: '7',
      price: '',
      duration: '',
      nickname: '',
      allowBooking: true,
      advanceBookingDays: 0,
      minimumNoticeHours: 0,
      appointmentType: 'regular'
    }
  })

  // Fetch service details for update mode
  const { data: serviceData } = useQuery({
    queryKey: ['service', serviceId],
    queryFn: async () => {
      const res = await api.get(`/v1/admin/services/${serviceId}`)
      return res.data.data
    },
    enabled: isUpdateMode && isOpen && !!serviceId,
  })

  // Prefill form when service data is loaded (update mode)
  useEffect(() => {
    if (serviceData && isUpdateMode) {
      const serviceType = serviceData.service_mode === 'TELECONSULTATION' ? 'video' : 'in-clinic'
      const paymentMethod = serviceData.payment_type === 'PREPAID' ? 'pre-paid' : 'post-consultation'
      const appointmentType = serviceData.appointment_type?.toLowerCase() === 'followup' ? 'followup' : 'regular'
      const minimumNoticeHours = serviceData.minimum_notice_minutes ? Math.floor(serviceData.minimum_notice_minutes / 60) : 0

      reset({
        serviceName: serviceData.name || '',
        type: serviceType,
        paymentSettings: paymentMethod,
        price: serviceData.price ? String(serviceData.price) : '',
        duration: String(serviceData.duration || '15'),
        followup_validity: serviceData.follow_up_validity ? String(serviceData.follow_up_validity) : '7',
        nickname: serviceData.nickname || '',
        allowBooking: !!serviceData.is_bookable,
        advanceBookingDays: serviceData.advance_booking_days || 0,
        minimumNoticeHours: minimumNoticeHours,
        appointmentType: appointmentType
      })
    } else if (!isUpdateMode) {
      // Reset form for create mode
      reset({
        serviceName: '',
        type: 'in-clinic',
        paymentSettings: 'pre-paid',
        followup_validity: '7',
        price: '',
        duration: '',
        nickname: '',
        allowBooking: true,
        advanceBookingDays: 0,
        minimumNoticeHours: 0,
        appointmentType: 'regular'
      })
    }
  }, [serviceData, isUpdateMode, reset])

  const appointmentType = watch('appointmentType')
  const advanceBookingDays = watch('advanceBookingDays')
  const minimumNoticeHours = watch('minimumNoticeHours')

  const onSubmit = (formData: ServiceFormData) => {
    if (nameExists && !isUpdateMode) return

    // Use admin service creation/update for admin users
    if (isAdmin) {
      // Get clinic_id from user context or service data
      const clinicId = user?.clinic_id || serviceData?.clinic_id || ''

      if (!clinicId && !isUpdateMode) {
        toast.error('Clinic ID is required. Please ensure you are associated with a clinic.')
        return
      }

      if (isUpdateMode && serviceId) {
        // Update mode
        const appointmentType: 'REGULAR' | 'FOLLOW_UP' | undefined = formData.appointmentType
          ? (formData.appointmentType === 'followup' ? 'FOLLOW_UP' : 'REGULAR')
          : undefined

        const updatePayload = {
          type: (formData.type === 'in-clinic' ? 'visit' : 'video') as 'visit' | 'video',
          payment_method: (formData.paymentSettings === 'pre-paid' ? 'pre-paid' : 'post_consultation') as 'pre-paid' | 'post_consultation',
          prefer_not_to_define_price: 0,
          duration: formData.duration,
          allow_patient_booking: formData.allowBooking ? 1 : 0,
          has_advance_booking: (formData.advanceBookingDays && formData.advanceBookingDays > 0) ? 1 : 0,
          advance_booking_from: formData.advanceBookingDays ?? 0,
          minimum_notice: formData.minimumNoticeHours ?? 0,
          nickname: formData.nickname || undefined,
          appointment_type: appointmentType,
          follow_up_validity: formData.followup_validity || undefined,
          description: undefined,
          appointment_treatment_id: undefined,
          amount: formData.price && formData.price !== null ? Number(formData.price) : 0,
        }

        updateAdminServiceMutation.mutate(
          {
            serviceId,
            payload: updatePayload,
            clinicId: clinicId || undefined,
            serviceName: formData.serviceName
          },
          {
            onSuccess: () => {
              toast.success('Service updated successfully!')
              setIsOpen(false)
            },
            onError: (err: any) => {
              toast.error(err?.message || 'Failed to update service')
            }
          }
        )
      } else {
        // Create mode
        const adminPayload: CreateAdminServicePayload = {
          advance_booking_days: formData.advanceBookingDays || 0,
          appointment_type: formData.appointmentType === 'regular' ? 'REGULAR' : 'FOLLOWUP',
          clinic_id: clinicId,
          is_bookable: formData.allowBooking,
          minimum_notice_minutes: (formData.minimumNoticeHours || 0) * 60, // Convert hours to minutes
          name: formData.serviceName,
          nickname: formData.nickname || undefined,
          payment_type: formData.paymentSettings === 'pre-paid' ? 'PREPAID' : 'POSTPAID',
          price: Number(formData.price || 0),
          service_mode: formData.type === 'in-clinic' ? 'IN_CLINIC' : 'TELECONSULTATION'
        }

        createAdminServiceMutation.mutate(adminPayload, {
          onSuccess: () => setIsOpen(false)
        })
      }
    } else {
      createDoctorServiceMutation.mutate(formData)
    }
  }

  const serviceName = watch('serviceName')
  const nameExists = isAdmin && !isUpdateMode && calendarServices.some((s) => {
    if (!s) return false
    const serviceNameLower = (serviceName || '').toString().toLowerCase().trim()
    const serviceNameMatch = s.service_name ? s.service_name.toString().toLowerCase() === serviceNameLower : false
    const nicknameMatch = s.nickname ? s.nickname.toString().toLowerCase() === serviceNameLower : false
    return serviceNameMatch || nicknameMatch
  })

  return (
    <BaseSideSheet
      size="lg"
      title={isUpdateMode ? "Update Service" : "Create New Service"}
      isOpen={isOpen}
      onOpenChange={setIsOpen}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack gap="lg">
          {/* Service Name Combobox */}
          <Input.Wrapper
            label="Service Name"
            error={
              nameExists
                ? 'This service name already exists'
                : errors.serviceName?.message
            }
          >
            <Controller
              name="serviceName"
              control={control}
              render={({ field }) => {
                if (!isAdmin && !isUpdateMode) {
                  return (
                    <Select
                      {...field}
                      placeholder="Select service"
                      data={availableDoctorServices.map((service) => ({
                        value: service.id,
                        label: service.nickname
                          ? `${service.nickname} (${service.service_name})`
                          : service.service_name,
                      }))}
                      searchable
                      nothingFoundMessage="No services available"
                    />
                  )
                }

                return (
                  <Input
                    {...field}
                    placeholder="Enter service name"
                    disabled={isUpdateMode}
                    style={{
                      borderColor: nameExists ? '#fa5252' : undefined,
                      boxShadow: nameExists
                        ? '0 0 0 2px rgba(250, 82, 82, 0.15)'
                        : undefined
                    }}
                  />
                )
              }}
            />
          </Input.Wrapper>

          {/* Service Mode */}
          <Stack gap="sm">
            <Text fw={600}>Service Mode</Text>
            <Controller
              name="type"
              control={control}
              render={({ field }) => (
                <Radio.Group
                  {...field}
                  name="type"
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
                    styles={{
                      input: {
                        paddingLeft: '65px !important',
                      },
                    }}
                  />
                )}
              />
            </Input.Wrapper>
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
                  data={isAdmin
                    ? durationDropdownItems
                    : durationDropdownItems.filter(({ value }) => Number(value) >= 5)}
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

          {/* Create/Update Service Button */}
          <Group mt={'xl'}>
            <Button
              type="submit"
              fullWidth
              loading={isUpdateMode ? updateAdminServiceMutation.isPending : (createDoctorServiceMutation.isPending || createAdminServiceMutation.isPending)}
              disabled={nameExists || (isUpdateMode ? updateAdminServiceMutation.isPending : (createDoctorServiceMutation.isPending || createAdminServiceMutation.isPending))}
            >
              {isUpdateMode ? 'Update Service' : 'Create Service'}
            </Button>
          </Group>
        </Stack>
      </form>
    </BaseSideSheet>
  )
}

export default CreateNewService
