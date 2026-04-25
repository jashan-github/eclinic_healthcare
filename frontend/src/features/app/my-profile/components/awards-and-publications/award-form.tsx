import type { Award } from '@/types/award'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { Button, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useAwards } from '../../hooks/use-awards'
import { useAwardsStore } from '../../stores/use-awards-store'

const awardFormSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(2).max(100),
  year: z.string().length(4, { message: 'Please select a valid year' }),
  published_awarded_by: z.string().min(2).max(100)
})

const AwardForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, saveAward, updateAward } = useAwards()
  const { award, closeShowAwardForm, processCancel } = useAwardsStore()

  const awardForm = useForm<z.infer<typeof awardFormSchema>>({
    validate: zodResolver(awardFormSchema),
    initialValues: {
      id: award?.id || '',
      name: award?.name || '',
      year: award?.year || '',
      published_awarded_by: award?.published_awarded_by || ''
    }
  })

  const handleAddAward = (data: Award) => {
    saveAward(data, {
      onSuccess: () => {
        toast.success('Award added successfully')
        closeShowAwardForm()
      },
      onError: (error: Error) => {
        toast.error(`Failed to add award: ${error.message}`)
      }
    })
  }

  const handleEditAward = (data: Award) => {
    const awardId = awardForm.values.id
    if (!awardId) return

    updateAward(
      { awardId, data },
      {
        onSuccess: () => {
          closeShowAwardForm()
          toast.success('Award updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update award: ${error.message}`)
        }
      }
    )
  }

  return (
    <form
      onSubmit={awardForm.onSubmit(
        awardForm.values.id ? handleEditAward : handleAddAward
      )}
      className="space-y-8"
    >
      <TextInput
        label="Award Name"
        placeholder="Enter Name of Award"
        classNames={{ input: 'orvo-base-input' }}
        {...awardForm.getInputProps('name')}
      />

      <Select
        label="Year award received"
        placeholder="Select Year"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        styles={{ dropdown: { maxHeight: '400px', overflowY: 'auto' } }}
        {...awardForm.getInputProps('year')}
      />

      <TextInput
        label="Awarded by"
        placeholder="Enter Awarded by"
        classNames={{ input: 'orvo-base-input' }}
        {...awardForm.getInputProps('published_awarded_by')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          {award?.id ? 'Update' : 'Save'}
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

      {awardForm.errors.root && (
        <div className="text-red-500">{awardForm.errors.root}</div>
      )}
    </form>
  )
}

export default AwardForm
