// src/services/clinics.ts
import api from '@/lib/api'

export interface ClinicLocation {
  id: string
  name: string
  branch_type?: string
  address: string
  building_name?: string
  street_name?: string
  pincode?: string | null
  phone?: string
  email?: string
  country?: string
  state?: string
  city?: string
  country_id?: string
  state_id?: string
  city_id?: string
  latitude?: string | null
  longitude?: string | null
  is_primary?: boolean
  created_at?: string
  updated_at?: string
}

export interface ClinicsResponse {
  status: boolean
  message: string
  data: {
    locations: ClinicLocation[]
  }
}

export const fetchClinics = async (): Promise<ClinicsResponse> => {
  try {
    const response = await api.get<ClinicsResponse>('/v1/doctor/rx-templates/locations')
    return response.data
  } catch (error) {
    console.error('Failed to fetch clinic locations:', error)
    throw new Error('Unable to load clinic locations. Please try again.')
  }
}