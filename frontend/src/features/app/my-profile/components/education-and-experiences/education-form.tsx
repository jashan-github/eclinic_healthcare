import type { Education } from '@/types/education'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { Button, Select, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'
import { useEducations } from '../../hooks/use-educations'
import { useEducationsStore } from '../../stores/use-educations-store'

const formSchema = z.object({
  id: z.string().optional(),
  university: z.string().min(2).max(100),
  degree: z
    .string()
    .min(2, 'Degree must be at least 2 characters')
    .max(100, 'Degree must not exceed 100 characters'),
  year: z
    .string()
    .regex(/^\d{4}$/, 'Enter a valid year (e.g., 2023)')
    .refine(
      (v) => parseInt(v, 10) <= new Date().getFullYear(),
      'Year cannot be in the future'
    )
})

const EducationForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, saveEducation, updateEducation } =
    useEducations()
  const { education, closeShowEducationForm, processCancel } =
    useEducationsStore()

  const educationForm = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      id: education?.id || '',
      university: education?.university || '',
      degree: education?.degree || '',
      year: education?.year || ''
    }
  })

  const handleAddEducation = (data: Education) => {
    saveEducation(data, {
      onSuccess: () => {
        toast.success('Education added successfully')
        closeShowEducationForm()
      },
      onError: (error: Error) => {
        toast.error(`Failed to add education: ${error.message}`)
      }
    })
  }

  const handleEditEducation = (data: Education) => {
    const educationId = educationForm.values.id
    if (!educationId) {
      console.error('handleEditEducation called without an educationId')
      toast.error('Unable to update — please refresh and try again')
      return
    }

    updateEducation(
      { educationId, data },
      {
        onSuccess: () => {
          closeShowEducationForm()
          toast.success('Education updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update education: ${error.message}`)
        }
      }
    )
  }

  return (
    <form
      onSubmit={educationForm.onSubmit(
        educationForm.values.id ? handleEditEducation : handleAddEducation
      )}
      className="space-y-8"
    >
      <TextInput
        label="College / University Name"
        placeholder="Enter Your College/University Name"
        classNames={{ input: 'orvo-base-input' }}
        {...educationForm.getInputProps('university')}
      />

      <TextInput
        label="Degree"
        placeholder="Enter Degree"
        classNames={{ input: 'orvo-base-input' }}
        {...educationForm.getInputProps('degree')}
      />

      <Select
        label="Year of Passing"
        placeholder="Select Year of Passing"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        styles={{ dropdown: { maxHeight: '400px', overflowY: 'auto' } }}
        {...educationForm.getInputProps('year')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          {education?.id ? 'Update' : 'Save'}
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

      {educationForm.errors.root && (
        <div className="text-red-500">{educationForm.errors.root}</div>
      )}
    </form>
  )
}

export default EducationForm
