import ErrorWhileFetchingData from '@/components/orvo/common/error-while-fetching-data'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useSocialLinks } from '@/features/app/my-profile/hooks/use-social-links'
import { Button, TextInput } from '@mantine/core'
import { useForm } from '@mantine/form'
import { zodResolver } from 'mantine-form-zod-resolver'
import { useEffect, type FC, type ReactElement } from 'react'
import { toast } from 'react-toastify'
import { z } from 'zod'

const formSchema = z.object({
  facebook_link: z
    .string()
    .optional()
    .refine((val) => !val || z.url().safeParse(val).success, {
      message: 'Invalid URL'
    }),
  linkedIn_link: z
    .string()
    .optional()
    .refine((val) => !val || z.url().safeParse(val).success, {
      message: 'Invalid URL'
    }),
  instagram_link: z
    .string()
    .optional()
    .refine((val) => !val || z.url().safeParse(val).success, {
      message: 'Invalid URL'
    }),
  youTube_link: z
    .string()
    .optional()
    .refine((val) => !val || z.url().safeParse(val).success, {
      message: 'Invalid URL'
    })
})

const LinkYourSocials: FC = (): ReactElement => {
  const { socialLinks, isLoading, error, saveSocialLinks, isSaving } =
    useSocialLinks()

  const linkYourSocialForm = useForm<z.infer<typeof formSchema>>({
    validate: zodResolver(formSchema),
    initialValues: {
      facebook_link: socialLinks?.facebook_link || '',
      linkedIn_link: socialLinks?.linkedIn_link || '',
      instagram_link: socialLinks?.instagram_link || '',
      youTube_link: socialLinks?.youTube_link || ''
    }
  })

  useEffect(() => {
    if (socialLinks) {
      linkYourSocialForm.setValues({
        facebook_link: socialLinks.facebook_link || '',
        linkedIn_link: socialLinks.linkedIn_link || '',
        instagram_link: socialLinks.instagram_link || '',
        youTube_link: socialLinks.youTube_link || ''
      })
      linkYourSocialForm.resetDirty()
    }
  }, [socialLinks, linkYourSocialForm])

  const submitForm = (values: z.infer<typeof formSchema>) => {
    const sanitizedValues = {
      facebook_link: values.facebook_link ?? '',
      linkedIn_link: values.linkedIn_link ?? '',
      instagram_link: values.instagram_link ?? '',
      youTube_link: values.youTube_link ?? ''
    }

    saveSocialLinks(sanitizedValues, {
      onSuccess: () => {
        toast.success('Social links saved successfully!')
      },
      onError: () => {
        toast.error('Failed to save social links.')
      }
    })
  }

  if (isLoading) return <GlobalLoader />
  if (error) return <ErrorWhileFetchingData />

  return (
    <form
      onSubmit={linkYourSocialForm.onSubmit(submitForm)}
      className="space-y-8 overflow-y-scroll p-4"
    >
      <TextInput
        label="Facebook (Optional)"
        placeholder="Paste your Facebook profile link here"
        classNames={{ input: 'orvo-base-input' }}
        {...linkYourSocialForm.getInputProps('facebook_link')}
      />

      <TextInput
        label="LinkedIn (Optional)"
        placeholder="Paste your LinkedIn profile link here"
        classNames={{ input: 'orvo-base-input' }}
        {...linkYourSocialForm.getInputProps('linkedIn_link')}
      />

      <TextInput
        label="Instagram (Optional)"
        placeholder="Paste your Instagram profile link here"
        classNames={{ input: 'orvo-base-input' }}
        {...linkYourSocialForm.getInputProps('instagram_link')}
      />

      <TextInput
        label="YouTube (Optional)"
        placeholder="Paste your YouTube profile link here"
        classNames={{ input: 'orvo-base-input' }}
        {...linkYourSocialForm.getInputProps('youTube_link')}
      />

      <Button
        className="w-full"
        loading={isSaving}
        type="submit"
      >
        Save
      </Button>

      {linkYourSocialForm.errors.root && (
        <div className="text-red-500">{linkYourSocialForm.errors.root}</div>
      )}
    </form>
  )
}

export default LinkYourSocials
