import type { Publication } from '@/types/publication'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { Button, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { usePublications } from '../../hooks/use-publications'
import { usePublicationsStore } from '../../stores/use-publications-store'

const publicationFormSchema = z.object({
  id: z.string().optional(),
  name: z.string().min(2).max(100),
  year: z.string().length(4, { message: 'Please select a valid year' }),
  published_awarded_by: z.string().min(2).max(100)
})

const PublicationForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, savePublication, updatePublication } =
    usePublications()
  const { publication, closeShowPublicationForm, processCancel } =
    usePublicationsStore()

  const publicationForm = useForm<z.infer<typeof publicationFormSchema>>({
    validate: zodResolver(publicationFormSchema),
    initialValues: {
      id: publication?.id || '',
      name: publication?.name || '',
      year: publication?.year || '',
      published_awarded_by: publication?.published_awarded_by || ''
    }
  })

  const handleAddPublication = (data: Publication) => {
    savePublication(data, {
      onSuccess: () => {
        toast.success('Publication added successfully')
        closeShowPublicationForm()
      },
      onError: (error: Error) => {
        toast.error(`Failed to add publication: ${error.message}`)
      }
    })
  }

  const handleEditPublication = (data: Publication) => {
    const publicationId = publicationForm.values.id
    if (!publicationId) return

    updatePublication(
      { publicationId, data },
      {
        onSuccess: () => {
          closeShowPublicationForm()
          toast.success('Publication updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update publication: ${error.message}`)
        }
      }
    )
  }

  return (
    <form
      onSubmit={publicationForm.onSubmit(
        publicationForm.values.id ? handleEditPublication : handleAddPublication
      )}
      className="space-y-8"
    >
      <TextInput
        label="Topic/Name of paper"
        placeholder="Enter Topic/Name of paper"
        classNames={{ input: 'orvo-base-input' }}
        {...publicationForm.getInputProps('name')}
      />

      <Select
        label="Year of Publication"
        placeholder="Select Year of Publication"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        styles={{ dropdown: { maxHeight: '400px', overflowY: 'auto' } }}
        {...publicationForm.getInputProps('year')}
      />

      <TextInput
        label="Published In"
        placeholder="Enter Published In"
        classNames={{ input: 'orvo-base-input' }}
        {...publicationForm.getInputProps('published_awarded_by')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          {publication?.id ? 'Update' : 'Save'}
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

      {publicationForm.errors.root && (
        <div className="text-red-500">{publicationForm.errors.root}</div>
      )}
    </form>
  )
}

export default PublicationForm
