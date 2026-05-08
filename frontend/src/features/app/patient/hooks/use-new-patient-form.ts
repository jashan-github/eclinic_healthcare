import { useForm } from '@tanstack/react-form'
import { useEffect, useState } from 'react'
import { z } from 'zod'
import { generateUHIDForNewPatient } from '../../patients/services/patients-service'

const SALUTATIONS = ['Mr', 'Ms', 'Mrs', 'Dr', 'Other'] as const

const schema = z
  .object({
    country_code: z
      .string()
      .regex(/^\d{1,4}$/, 'Select a country')
      .min(1, 'Country code is required'),
    phone: z
      .string()
      .regex(/^\d{4,15}$/, 'Phone number must be 4-15 digits'),
    salutation: z.enum(['Mr', 'Ms', 'Mrs', 'Dr', 'Other']).optional(),
    first_name: z.string().min(1, 'First name is required'),
    middle_name: z.string().optional(),
    last_name: z.string().optional(),
    age: z
      .string()
      .regex(/^\d{1,3}$/, 'Age must be a number')
      .or(z.literal(''))
      .optional(),
    dob: z
      .string()
      .refine(
        (v) => {
          if (!v) return true
          const d = new Date(v)
          return !Number.isNaN(d.getTime()) && d.getTime() <= Date.now()
        },
        { message: 'Date of birth must be a valid date in the past' }
      )
      .optional(),
    gender: z.enum(['male', 'female', 'other']),
    uhid: z
      .string()
      .min(1, 'UHID is required — click Generate to create one'),
    address: z.string().min(1, 'Address is required').or(z.literal('')).optional(),
    city: z.string().min(1, 'City is required').or(z.literal('')).optional(),
    pincode: z
      .string()
      .min(3, 'Pincode is too short')
      .max(10, 'Pincode is too long')
      .or(z.literal(''))
      .optional(),
    relationship_with_patient: z.string().optional(),
    blood_group: z.string().optional(),
    referred_by_doctor: z.string().optional(),
    alternate_phone_number: z.string().optional(),
    occupation: z.string().optional(),
    name_of_informant: z.string().optional(),
    channel: z.string().optional(),
    religion: z.string().optional(),
    marital_status: z.string().optional(),
    preferred_language: z.string().optional(),
    email: z
      .string()
      .email('Please enter a valid email address')
      .or(z.literal(''))
      .optional()
  })
  .superRefine((data, ctx) => {
    // age ↔ dob consistency: if both provided, computed age from dob must be
    // within ±1 year of the entered age (allow off-by-one for birthday timing).
    if (data.age && data.dob) {
      const ageNum = parseInt(data.age, 10)
      const dobDate = new Date(data.dob)
      if (Number.isFinite(ageNum) && !Number.isNaN(dobDate.getTime())) {
        const today = new Date()
        let computedAge = today.getFullYear() - dobDate.getFullYear()
        const monthDelta = today.getMonth() - dobDate.getMonth()
        if (
          monthDelta < 0 ||
          (monthDelta === 0 && today.getDate() < dobDate.getDate())
        ) {
          computedAge--
        }
        if (Math.abs(computedAge - ageNum) > 1) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Age (${ageNum}) does not match date of birth (computed age ${computedAge})`,
            path: ['age']
          })
        }
      }
    }
  })

const defaultValues = {
  country_code: '91',
  phone: '',
  salutation: 'Mr' as 'Mr' | 'Ms' | 'Mrs' | 'Dr' | 'Other',
  first_name: '',
  middle_name: '',
  last_name: '',
  age: '',
  dob: '',
  gender: 'male' as 'male' | 'female' | 'other',
  uhid: '',
  address: '',
  city: '',
  pincode: '',
  relationship_with_patient: '',
  blood_group: '',
  referred_by_doctor: '',
  alternate_phone_number: '',
  occupation: '',
  name_of_informant: '',
  channel: '',
  religion: '',
  marital_status: '',
  preferred_language: '',
  email: ''
}

interface UseNewPatientFormProps {
  isMedicalHistory?: boolean
}

export const useNewPatientForm = ({
  isMedicalHistory
}: UseNewPatientFormProps) => {
  const [noKnownMedicalHistory, setNoKnownMedicalHistory] = useState(
    isMedicalHistory ?? false
  )
  const [isGeneratingUHID, setIsGeneratingUHID] = useState(false)

  const form = useForm({
    defaultValues,
    validators: {
      onSubmit: ({ value }) => {
        const result = schema.safeParse(value)
        if (!result.success) {
          // TanStack Form v1 expects { fields: { fieldName: error } } so each
          // <form.Field> reads its own error via state.meta.errors.
          return { fields: result.error.flatten().fieldErrors }
        }
        return undefined
      }
    },
    onSubmit: async () => {
      // submission handled by the consuming component
    }
  })

  const generateUHIDForPatient = async (): Promise<void> => {
    try {
      setIsGeneratingUHID(true)
      const { uhid } = await generateUHIDForNewPatient()
      form.setFieldValue('uhid', uhid)
    } finally {
      setIsGeneratingUHID(false)
    }
  }

  useEffect(() => {
    if (isMedicalHistory !== undefined) {
      setNoKnownMedicalHistory(isMedicalHistory)
    }
  }, [isMedicalHistory])

  return {
    form,
    noKnownMedicalHistory,
    setNoKnownMedicalHistory,
    isGeneratingUHID,
    generateUHIDForPatient,
    SALUTATIONS
  }
}
