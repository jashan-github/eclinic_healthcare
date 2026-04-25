import { Button, Select, TextInput } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import { useForm } from '@mantine/form'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useMemberships } from '../../../hooks/use-memberships'
import { useMembershipStore } from '../../../stores/use-membership-store'
import type { Membership } from '@/types/membership'
import { yearsList, yearsListTillCurrentYear } from '@/utils/year-list'
import { zodResolver } from 'mantine-form-zod-resolver'

const formSchema = z
  .object({
    id: z.string().optional(),
    organization_name: z
      .string()
      .min(2, 'Organization name must be at least 2 characters')
      .max(100, 'Organization name must not exceed 100 characters'),
    member_from: z.string().length(4, 'Select a valid year'),
    member_till: z.string().length(4, 'Select a valid year')
  })
  .refine((data) => parseInt(data.member_from) <= parseInt(data.member_till), {
    message: 'Member From year must be less than or equal to Member To year',
    path: ['member_till']
  })

const MembershipForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, saveMembership, updateMembership } =
    useMemberships()
  const { membership, processCancel, setMembership } = useMembershipStore()

  const membershipForm = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      id: membership?.id || '',
      organization_name: membership?.organization_name || '',
      member_from: membership?.member_from || '',
      member_till: membership?.member_till || ''
    }
  })

  const handleAddMembership = (data: Membership) => {
    saveMembership(data, {
      onSuccess: () => {
        setMembership(null)
        toast.success('Membership added successfully')
      },
      onError: (error: Error) => {
        toast.error(`Failed to add membership: ${error.message}`)
      }
    })
  }

  const handleEditMembership = (data: Membership) => {
    const membershipId = membershipForm.values.id
    if (!membershipId) return

    updateMembership(
      { membershipId, data },
      {
        onSuccess: () => {
          setMembership(null)
          toast.success('Membership updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update membership: ${error.message}`)
        }
      }
    )
  }

  return (
    <form
      onSubmit={membershipForm.onSubmit(
        membershipForm.values.id ? handleEditMembership : handleAddMembership
      )}
      className="space-y-8 px-1"
    >
      <TextInput
        label="Member Of"
        placeholder="Enter name of Organization"
        classNames={{ input: 'orvo-base-input' }}
        {...membershipForm.getInputProps('organization_name')}
      />

      <Select
        label="Member From"
        placeholder="Select Year"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        styles={{ dropdown: { maxHeight: '400px', overflowY: 'auto' } }}
        {...membershipForm.getInputProps('member_from')}
      />

      <Select
        label="Member To"
        placeholder="Select Year"
        data={yearsList().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        {...membershipForm.getInputProps('member_till')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          'Save'
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

      {membershipForm.errors.root && (
        <div className="text-red-500">{membershipForm.errors.root}</div>
      )}
    </form>
  )
}

export default MembershipForm
