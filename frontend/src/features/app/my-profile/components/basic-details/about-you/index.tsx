import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useBasicDetails } from '@/features/app/my-profile/hooks/use-basic-details'
import { useLanguages } from '@/hooks/use-languages'
import type { Language } from '@/types/language'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button, TextInput, Textarea } from '@mantine/core'
import { type FC, type ReactElement, useEffect } from 'react'
import { Controller, useFieldArray, useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { z } from 'zod'
import LanguageSelector from './_partials/language-selector'

const LanguageSchema = z.object({
  id: z.string(),
  language_name: z.string(),
  language_code: z.string()
})

const aboutYouFormSchema = z.object({
  years_of_experience: z
    .string()
    .regex(/^\d+$/, 'Must be a valid number')
    .refine((val) => {
      const num = parseInt(val)
      return num >= 1 && num <= 50
    }, 'Must be between 1 and 50 years'),
  intro: z
    .string()
    .min(
      10,
      'Intro must be at least 10 characters for better patient engagement'
    )
    .max(100, 'Intro cannot exceed 100 characters'),
  about: z
    .string()
    .min(
      50,
      'Please provide a more detailed description (at least 50 characters)'
    )
    .max(500, 'Description cannot exceed 500 characters'),
  languages: z.array(LanguageSchema)
})

type FormValues = z.infer<typeof aboutYouFormSchema>

const AboutYou: FC = (): ReactElement => {
  const { basicDetails, isLoading, error, saveBasicDetails, isSaving } =
    useBasicDetails()
  const { languages } = useLanguages()

  // Initialize React Hook Form
  const form = useForm<FormValues>({
    resolver: zodResolver(aboutYouFormSchema),
    defaultValues: {
      years_of_experience: '',
      intro: '',
      about: '',
      languages: []
    }
  })

  // Field array for languages
  const {
    fields: selectedLanguages,
    append,
    remove
  } = useFieldArray({
    control: form.control,
    name: 'languages'
  })

  // Sync form with basicDetails
  useEffect(() => {
    if (basicDetails) {
      form.reset(basicDetails)
    }
  }, [basicDetails, form])

  // Handle form submission
  const onSubmit = async (data: FormValues) => {
    await saveBasicDetails(data, {
      onSuccess: () => {
        toast.success('Your information has been updated successfully.')
        form.reset(data, { keepValues: true, keepDirty: false })
      },
      onError: (error: Error) => {
        toast.error('Failed to update information. Please try again.')
        console.error('Save failed:', error)
      }
    })
  }

  // Available languages (excluding selected ones)
  const availableLanguages =
    languages?.filter(
      (lang) => !selectedLanguages.some((selected) => selected.id === lang.id)
    ) || []

  // Add and remove language handlers
  const addLanguage = (language: Language) => {
    if (!selectedLanguages.some((lang) => lang.id === language.id)) {
      append(language)
    }
  }

  const removeLanguage = (language: Language) => {
    const index = selectedLanguages.findIndex((lang) => lang.id === language.id)
    if (index !== -1) {
      remove(index)
    }
  }

  if (isLoading) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <div className="py-4 px-2 flex flex-col gap-4">
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="space-y-8"
      >
        <Controller
          name="years_of_experience"
          control={form.control}
          render={({ field, fieldState }) => (
            <TextInput
              {...field}
              label="Years of Experience"
              placeholder="Enter your years of experience"
              classNames={{ input: 'orvo-base-input' }}
              error={fieldState.error?.message}
            />
          )}
        />

        <Controller
          name="intro"
          control={form.control}
          render={({ field, fieldState }) => (
            <TextInput
              {...field}
              label="Your Intro"
              placeholder="This is the first thing that patients see..."
              classNames={{ input: 'orvo-base-input' }}
              error={fieldState.error?.message}
            />
          )}
        />

        <Controller
          name="about"
          control={form.control}
          render={({ field, fieldState }) => (
            <Textarea
              {...field}
              label="About You"
              placeholder="Add your experience, achievements and more..."
              rows={10}
              error={fieldState.error?.message}
            />
          )}
        />

        <div>
          <label className="text-sm font-medium mb-2 block">
            Languages you speak
          </label>
          <LanguageSelector
            availableLanguages={availableLanguages}
            selectedLanguages={selectedLanguages}
            onAdd={addLanguage}
            onRemove={removeLanguage}
          />
          {form.formState.errors.languages && (
            <div className="text-red-500 text-sm mt-1">
              {form.formState.errors.languages.message}
            </div>
          )}
        </div>

        <Button
          type="submit"
          fullWidth
          loading={isSaving}
          aria-label={isSaving ? 'Saving' : 'Save'}
        >
          Save
        </Button>
      </form>
    </div>
  )
}

export default AboutYou
