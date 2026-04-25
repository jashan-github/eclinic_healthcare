import { Button, Select, TextInput } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import { useForm } from '@mantine/form'
import { z } from 'zod'
import { useExperiences } from '../../hooks/use-experiences'
import { useExperiencesStore } from '../../stores/use-experiences-store'
import type { Experience } from '@/types/experience'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { zodResolver } from 'mantine-form-zod-resolver'
import { toast } from 'react-toastify'

const formSchema = z.object({
  id: z.string().optional(),
  title: z.string().min(2).max(100),
  clinic_hospital_name: z.string().min(2).max(100), // Fixed length(4) to min(2).max(100) for consistency
  start_from: z.string().length(4, 'Select a valid year'),
  end_year: z.string().length(4, 'Select a valid year')
})

const ExperienceForm: FC = (): ReactElement => {
  const { isSaving, isUpdating, saveExperience, updateExperience } =
    useExperiences()
  const { experience, closeShowExperienceForm, processCancel } =
    useExperiencesStore()

  const experienceForm = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      id: experience?.id || '',
      title: experience?.title || '',
      clinic_hospital_name: experience?.clinic_hospital_name || '',
      start_from: experience?.start_from || '',
      end_year: experience?.end_year || ''
    }
  })

  const handleAddExperience = (data: Experience) => {
    saveExperience(data, {
      onSuccess: () => {
        toast.success('Experience added successfully')
        closeShowExperienceForm()
      },
      onError: (error: Error) => {
        toast.error(`Failed to add experience: ${error.message}`)
      }
    })
  }

  const handleEditExperience = (data: Experience) => {
    const experienceId = experienceForm.values.id
    if (!experienceId) return

    updateExperience(
      { experienceId, data },
      {
        onSuccess: () => {
          closeShowExperienceForm()
          toast.success('Experience updated successfully')
        },
        onError: (error: Error) => {
          toast.error(`Failed to update experience: ${error.message}`)
        }
      }
    )
  }

  return (
    <form
      onSubmit={experienceForm.onSubmit(
        experienceForm.values.id ? handleEditExperience : handleAddExperience
      )}
      className="space-y-8"
    >
      <TextInput
        label="Title"
        placeholder="Enter Your Role's Title"
        classNames={{ input: 'orvo-base-input' }}
        {...experienceForm.getInputProps('title')}
      />

      <TextInput
        label="Hospital/Clinic"
        placeholder="Enter Hospital/Clinic Name"
        classNames={{ input: 'orvo-base-input' }}
        {...experienceForm.getInputProps('clinic_hospital_name')}
      />

      <Select
        label="Start Year"
        placeholder="Select Year"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        styles={{ dropdown: { maxHeight: '400px', overflowY: 'auto' } }}
        {...experienceForm.getInputProps('start_from')}
      />

      <Select
        label="End Year"
        placeholder="Select Year"
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        {...experienceForm.getInputProps('end_year')}
      />

      <div className="flex gap-2 w-full">
        <Button
          variant="outline"
          className="flex grow"
          loading={isSaving || isUpdating}
          type="submit"
        >
          {experience?.id ? 'Update' : 'Save'}
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

      {experienceForm.errors.root && (
        <div className="text-red-500">{experienceForm.errors.root}</div>
      )}
    </form>
  )
}

export default ExperienceForm
