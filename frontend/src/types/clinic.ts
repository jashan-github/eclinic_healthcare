import type { Address } from './address'

export type Clinic = {
  id: string
  c_id: string | null
  timing: string
  name: string
  logo: string
  email: string | null
  phone_code: number
  phone: string
  owner_name: string
  health_services: string[]
  fees: string
  clinic_fee: {
    min: string
    max: string
  }
  isOwner: boolean
  address: Address
  primary_address: Address
  other_address: Address[]
  amenities: AmenityCategory[]
  specializations: string[]
  connected_status: string
  requestId: string
}

export type ClinicPhotoType =
  | 'identity'
  | 'interior'
  | 'exterior'
  | 'with-patient'

export type ClinicPhoto = {
  id: string
  image: string
  type: ClinicPhotoType
}

export type ClinicPhotoRaw = {
  type: ClinicPhotoType
  image: File
}

export type Amenity = {
  id: string
  parent?: string
  name: string
  status?: number
  created_at?: string
  updated_at?: string
  is_checked: boolean
}

export type AmenityCategory = {
  id: string
  parent?: string
  name: string
  status?: number
  created_at?: string
  updated_at?: string
  amenities: Amenity[]
}
