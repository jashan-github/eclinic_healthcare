import { type FC, useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Modal, Button, Textarea, Stack, Group } from '@mantine/core'
import type { SoapNote } from '@/services/doctor-soap-notes-service'

const soapNoteSchema = z.object({
  subjective: z.string().min(1, 'Subjective is required'),
  objective: z.string().min(1, 'Objective is required'),
  assessment: z.string().min(1, 'Assessment is required'),
  plan: z.string().min(1, 'Plan is required'),
})

type SoapNoteFormData = z.infer<typeof soapNoteSchema>

interface SoapNotesFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: SoapNoteFormData) => void
  isLoading?: boolean
  soapNote?: SoapNote | null
  mode: 'create' | 'edit'
}

const SoapNotesFormModal: FC<SoapNotesFormModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
  soapNote,
  mode
}) => {
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors }
  } = useForm<SoapNoteFormData>({
    resolver: zodResolver(soapNoteSchema),
    defaultValues: {
      subjective: '',
      objective: '',
      assessment: '',
      plan: ''
    }
  })

  useEffect(() => {
    if (soapNote && mode === 'edit') {
      reset({
        subjective: soapNote.subjective,
        objective: soapNote.objective,
        assessment: soapNote.assessment,
        plan: soapNote.plan
      })
    } else {
      reset({
        subjective: '',
        objective: '',
        assessment: '',
        plan: ''
      })
    }
  }, [soapNote, mode, reset])

  const handleFormSubmit = (data: SoapNoteFormData) => {
    onSubmit(data)
  }

  return (
    <Modal
      opened={isOpen}
      onClose={onClose}
      title={
        <span className="font-poppins font-semibold text-lg text-[#0F1011]">
          {mode === 'create' ? 'Add New SOAP Note' : 'Edit SOAP Note'}
        </span>
      }
      size="lg"
      centered
    >
      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <Stack gap="md">
          {/* Subjective */}
          <div>
            <label className="font-poppins font-semibold text-sm text-[#0F1011] mb-1 block">
              S - Subjective
            </label>
            <Controller
              name="subjective"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  placeholder="Patient's symptoms and complaints (e.g., Feeling feverish, Symptom: Chest wall)"
                  minRows={3}
                  error={errors.subjective?.message}
                  disabled={isLoading}
                />
              )}
            />
          </div>

          {/* Objective */}
          <div>
            <label className="font-poppins font-semibold text-sm text-[#0F1011] mb-1 block">
              O - Objective
            </label>
            <Controller
              name="objective"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  placeholder="Clinical findings and observations (e.g., High temperature 90°, Color of face changes)"
                  minRows={3}
                  error={errors.objective?.message}
                  disabled={isLoading}
                />
              )}
            />
          </div>

          {/* Assessment */}
          <div>
            <label className="font-poppins font-semibold text-sm text-[#0F1011] mb-1 block">
              A - Assessment
            </label>
            <Controller
              name="assessment"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  placeholder="Diagnosis (e.g., Infection by malaria, Mulberry molar)"
                  minRows={3}
                  error={errors.assessment?.message}
                  disabled={isLoading}
                />
              )}
            />
          </div>

          {/* Plan */}
          <div>
            <label className="font-poppins font-semibold text-sm text-[#0F1011] mb-1 block">
              P - Plan
            </label>
            <Controller
              name="plan"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  placeholder="Treatment plan (e.g., Suggested: DOLO 650 for 10 days)"
                  minRows={3}
                  error={errors.plan?.message}
                  disabled={isLoading}
                />
              )}
            />
          </div>

          {/* Buttons */}
          <Group justify="flex-end" mt="md">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" loading={isLoading}>
              {mode === 'create' ? 'Create' : 'Update'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}

export default SoapNotesFormModal

