import type { Language } from './language'

export type BasicDetails = {
  years_of_experience: string
  intro: string
  about: string
  languages: Language[]
}

export type DoctorDetails = {
  id: string
  name: string
  clinic_id: string
  short_description: string
  experience: string
  education: string
  email: string
  phone_code: number
  phone_number: string
  gender: string
  profile_img: string
  isWritingPad: boolean | null
  total_credits: number
  availableCredits: number
  available_credits: boolean
}
