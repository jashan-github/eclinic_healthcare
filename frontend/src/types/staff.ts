export type Staff = {
  id: string
  email: string
  first_name: string
  mobile: string
  middle_name: string
  last_name: string
  date_of_birth: string
  gender: 'male' | 'female' | 'other'
  clinics: string[]
  doctors: string[]
  is_admin: boolean
  role?: string
  name?: string
  phone_number?: string
  password?: string
  country_id?: string
  state_id?: string
  city_id?: string
  clinic_id?: string
}

export type StaffRaw = Omit<Staff, 'id'>

export type StaffResponse = {
  records: Staff[]
  total: number
  skip: number
  limit: number
}

export type StaffRole =
  | 'Queue Module'
  | 'Registration Module'
  | 'Patient'
  | 'Doctor'
  | 'Data Entry'
  | 'Pharmacy'
