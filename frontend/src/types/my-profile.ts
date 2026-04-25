import type { Clinic } from '@/types/clinic'

export type Profile = {
  id: string
  first_name: string
  middle_name: string
  last_name: string
  name: string
  full_name: string
  dob?: string
  date_of_birth?: string
  education: string
  profile_img_url: string
  fee: number | null
  address: string | null
  country: string
  state: string
  city: string
  country_id: string
  state_id: string
  city_id: string
  on_board_doctor: boolean
  invite_code: string
  invite_link: string
  years_of_experience: string
  intro: string
  about: string
  languages: string[]
  specializations: string[]
  major_specialization: string | null
  practice_areas: string[]
  commonly_treats: string[]
  facebook_link: string | null
  linkedIn_link: string | null
  instagram_link: string | null
  youTube_link: string | null
  active_clinic: Pick<Clinic, 'name' | 'logo' | 'address' | 'primary_address'> | null
  profile_img?: string

  // ====== NEW FIELDS ADDED FROM API (NO DELETION) ======
  email?: string
  phone_code?: number
  phone_number?: string
  gender?: string
  short_description?: string | null
  registration?: {
    regNo_degree: string
    council_university: string
    year: string
    file: string
  } | null
  // `educations` array already handled in service → converted to string
  // `clinics` array → `active_clinic` already mapped
}