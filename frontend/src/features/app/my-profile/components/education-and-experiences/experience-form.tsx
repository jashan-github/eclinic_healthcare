import { Button, Checkbox, Select, TextInput } from '@mantine/core'
import { type FC, type ReactElement } from 'react'
import { useForm } from '@mantine/form'
import { z } from 'zod'
import { useExperiences } from '../../hooks/use-experiences'
import { useExperiencesStore } from '../../stores/use-experiences-store'
import type { Experience } from '@/types/experience'
import { yearsListTillCurrentYear } from '@/utils/year-list'
import { zodResolver } from 'mantine-form-zod-resolver'
import { toast } from 'react-toastify'

const formSchema = z
  .object({
    id: z.string().optional(),
    title: z.string().min(2).max(100),
    clinic_hospital_name: z.string().min(2).max(100),
    start_from: z
      .string()
      .regex(/^\d{4}$/, 'Select a valid year')
      .refine(
        (v) => parseInt(v, 10) <= new Date().getFullYear(),
        'Start year cannot be in the future'
      ),
    // When is_current=true, end_year is allowed to be empty (ongoing role).
    end_year: z.string(),
    is_current: z.boolean()
  })
  .superRefine((data, ctx) => {
    if (data.is_current) {
      return // skip end_year validation entirely for ongoing roles
    }
    if (!/^\d{4}$/.test(data.end_year)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Select a valid year',
        path: ['end_year']
      })
      return
    }
    const endNum = parseInt(data.end_year, 10)
    if (endNum > new Date().getFullYear()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'End year cannot be in the future',
        path: ['end_year']
      })
      return
    }
    if (endNum < parseInt(data.start_from, 10)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'End year must be on or after start year',
        path: ['end_year']
      })
    }
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
      end_year: experience?.end_year || '',
      // An existing record with no end_year is treated as currently-ongoing.
      is_current: !!experience && !experience.end_year
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
    if (!experienceId) {
      console.error('handleEditExperience called without an experienceId')
      toast.error('Unable to update — please refresh and try again')
      return
    }

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

  const isCurrent = experienceForm.values.is_current

  // Normalize the data on submit: an ongoing role must send an empty
  // end_year so the backend recognizes it as the current position.
  const handleSubmit = (values: z.infer<typeof formSchema>) => {
    const payload: Experience = {
      ...values,
      end_year: values.is_current ? '' : values.end_year
    } as Experience
    if (values.id) {
      handleEditExperience(payload)
    } else {
      handleAddExperience(payload)
    }
  }

  return (
    <form
      onSubmit={experienceForm.onSubmit(handleSubmit)}
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

      <Checkbox
        label="I currently work here"
        {...experienceForm.getInputProps('is_current', { type: 'checkbox' })}
        onChange={(e) => {
          const checked = e.currentTarget.checked
          experienceForm.setFieldValue('is_current', checked)
          if (checked) {
            experienceForm.setFieldValue('end_year', '')
          }
        }}
      />

      <Select
        label="End Year"
        placeholder={isCurrent ? 'Ongoing' : 'Select Year'}
        data={yearsListTillCurrentYear().map((year) => year.toString())}
        classNames={{ input: 'orvo-base-input' }}
        disabled={isCurrent}
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
