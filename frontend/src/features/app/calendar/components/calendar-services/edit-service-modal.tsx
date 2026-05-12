import BaseSideSheet from '@/components/orvo/base-side-sheet'
import {
  Button,
  Group,
  Input,
  Radio,
  Select,
  Stack,
  Text
} from '@mantine/core'
import { useState, useEffect, type FC } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateDoctorServicePricing, createDoctorServicePricing, type UpdateDoctorServicePricingPayload, type CreateDoctorServicePricingPayload } from '@/services/weekly-schedule'
import { toast } from 'react-toastify'

// Curated currency list covering the markets the clinic serves.
// Backend accepts any ISO-4217 code; this is just what we expose in the UI.
const CURRENCY_OPTIONS = [
  { value: 'USD', label: 'USD ($)', symbol: '$' },
  { value: 'INR', label: 'INR (₹)', symbol: '₹' },
  { value: 'EUR', label: 'EUR (€)', symbol: '€' },
  { value: 'GBP', label: 'GBP (£)', symbol: '£' },
  { value: 'AED', label: 'AED (د.إ)', symbol: 'د.إ' },
  { value: 'CAD', label: 'CAD (C$)', symbol: 'C$' },
  { value: 'AUD', label: 'AUD (A$)', symbol: 'A$' },
  { value: 'SGD', label: 'SGD (S$)', symbol: 'S$' },
  { value: 'JPY', label: 'JPY (¥)', symbol: '¥' },
] as const

type CurrencyCode = (typeof CURRENCY_OPTIONS)[number]['value']

const getCurrencySymbol = (code: string): string =>
  CURRENCY_OPTIONS.find((c) => c.value === code)?.symbol ?? code

// Duration dropdown options
const durationDropdownItems = [
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
  { label: '90 Minutes', value: '90' },
  { label: '2 hours', value: '120' }
]

interface EditServiceModalProps {
  isOpen: boolean
  onClose: () => void
  service: {
    id: string
    service_name: string
    service_mode: string
    amount: number
    duration: number
    currency: string
    pricing_id?: string
  } | null
  onSuccess?: () => void
}

const EditServiceModal: FC<EditServiceModalProps> = ({
  isOpen,
  onClose,
  service,
  onSuccess
}) => {
  const queryClient = useQueryClient()
  const [serviceMode, setServiceMode] = useState<'IN_CLINIC' | 'TELECONSULTATION'>('IN_CLINIC')
  const [price, setPrice] = useState<string>('')
  const [duration, setDuration] = useState<string>('30')
  const [currency, setCurrency] = useState<CurrencyCode>('USD')

  // Update form when service changes
  useEffect(() => {
    if (service) {
      setServiceMode(service.service_mode === 'TELECONSULTATION' ? 'TELECONSULTATION' : 'IN_CLINIC')
      setPrice(String(service.amount || ''))
      setDuration(String(service.duration || '30'))
      const known = CURRENCY_OPTIONS.find((c) => c.value === service.currency)
      setCurrency(known ? (service.currency as CurrencyCode) : 'USD')
    }
  }, [service])

  const onMutationSuccess = async () => {
    // Clear all caches and force refetch
    queryClient.removeQueries({ queryKey: ['doctor-services'] })
    queryClient.removeQueries({ queryKey: ['doctorServicePricing'] })
    queryClient.removeQueries({ queryKey: ['doctor-service-pricing'] })
    queryClient.removeQueries({ queryKey: ['availabilityServicePricing'] })
    queryClient.removeQueries({ queryKey: ['availability-service-pricing'] })

    toast.success('Service updated successfully!')

    // Call onSuccess to trigger parent refetch
    if (onSuccess) {
      await onSuccess()
    }

    onClose()
  }

  const onMutationError = (error: any) => {
    toast.error(error?.message || 'Failed to update service')
  }

  const updatePricingMutation = useMutation({
    mutationFn: ({ pricingId, payload }: { pricingId: string, payload: UpdateDoctorServicePricingPayload }) =>
      updateDoctorServicePricing(pricingId, payload),
    onSuccess: onMutationSuccess,
    onError: onMutationError
  })

  const createPricingMutation = useMutation({
    mutationFn: (payload: CreateDoctorServicePricingPayload) =>
      createDoctorServicePricing(payload),
    onSuccess: onMutationSuccess,
    onError: onMutationError
  })

  const isSubmitting = updatePricingMutation.isPending || createPricingMutation.isPending

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedPrice = price.trim()
    const priceValue = parseFloat(trimmedPrice)
    if (!/^\d+(\.\d{1,2})?$/.test(trimmedPrice)) {
      toast.error('Enter a valid price (up to 2 decimal places)')
      return
    }
    if (!Number.isFinite(priceValue) || priceValue <= 0) {
      toast.error('Price must be greater than 0')
      return
    }

    if (service?.pricing_id) {
      // Update existing pricing record
      updatePricingMutation.mutate({
        pricingId: service.pricing_id,
        payload: {
          price_amount: priceValue
        }
      })
    } else if (service?.id) {
      // No pricing record exists yet — create one using the service_id
      createPricingMutation.mutate({
        service_id: service.id,
        price_amount: priceValue,
        currency: currency
      })
    } else {
      toast.error('Service ID not found. Cannot update pricing.')
    }
  }

  if (!service) return null

  return (
    <BaseSideSheet
      size="lg"
      title="Edit Service"
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose()
      }}
    >
      <form onSubmit={handleSubmit}>
        <Stack gap="lg" p="md">
          {/* Service Name (Read-only) */}
          <Stack gap="sm">
            <Text fw={600}>Service Name</Text>
            <Input
              value={service.service_name}
              disabled
              styles={{
                input: {
                  backgroundColor: '#f9fafb',
                  cursor: 'not-allowed'
                }
              }}
            />
          </Stack>

          {/* Service Mode */}
          <Stack gap="sm">
            <Text fw={600}>Service Mode</Text>
            <Radio.Group
              value={serviceMode === 'IN_CLINIC' ? 'in-clinic' : 'video'}
              onChange={(value) => setServiceMode(value === 'in-clinic' ? 'IN_CLINIC' : 'TELECONSULTATION')}
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
          </Stack>

          {/* Currency */}
          <Stack gap="sm">
            <Text fw={600}>Currency</Text>
            <Select
              data={CURRENCY_OPTIONS.map((c) => ({ value: c.value, label: c.label }))}
              value={currency}
              onChange={(value) => setCurrency((value as CurrencyCode) || 'USD')}
              searchable
              allowDeselect={false}
            />
          </Stack>

          {/* Price */}
          <Stack gap="sm">
            <Text fw={600}>Price</Text>
            <Input
              leftSection={<span className="text-sm">{getCurrencySymbol(currency)}</span>}
              placeholder="200"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              type="number"
              min="0.01"
              step="0.01"
            />
          </Stack>

          {/* Duration */}
          <Stack gap="sm">
            <Text fw={600}>Duration</Text>
            <Select
              placeholder="Select duration"
              data={durationDropdownItems}
              value={duration}
              onChange={(value) => setDuration(value || '30')}
            />
          </Stack>

          {/* Action Buttons */}
          <Group justify="flex-end" mt="xl">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              loading={isSubmitting}
            >
              Update
            </Button>
          </Group>
        </Stack>
      </form>
    </BaseSideSheet>
  )
}

export default EditServiceModal

