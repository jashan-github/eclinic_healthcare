import axiosInstance from '@/lib/api'

export interface PatientProfile {
  id: string
  full_name?: string
  first_name?: string
  middle_name?: string
  last_name?: string
  email: string
  dob?:string
  address?: string
  emergency_number?:string
  zip_code?:string
  contact_number?: string
  blood_group?:string
  profile_img?:string
  phone_number?: string
  phone_code?: number
  emergency_contact_number?: string
  family_contact_number?: string
  date_of_birth?: string
  blood_type?: string
  marital_status?: string
  occupation?: string
  preferred_language?: string
  preferred_language_id?: string
  gender?: string
  address_line_1?: string
  postal_code?: string
  country?: string
  country_id?: string
  city?: string
  city_id?: string
  state?: string
  state_id?: string
  profile_img_url?: string
  avatar?: string
}

interface ApiResponseData {
  status: boolean
  message: string
  data: {
    id?: string
    full_name?: string
    first_name?: string
    last_name?: string
    middle_name?: string
    email?: string
    phone_number?: string
    contact_number?: string
    phone_code?: number
    emergency_contact_number?: string
    family_contact_number?: string
    date_of_birth?: string
    blood_type?: string
    marital_status?: string
    occupation?: string
    preferred_language?: string
    gender?: string
    profile_img?: string
    profile_img_url?: string
    address?: string
    country?: string
    city?: string
    state?: string
    zip_code?: string
    invite_code?: string
    [key: string]: any
  }
}

export const getPatientProfileDetails = async (): Promise<PatientProfile> => {
  try {
    // Use the personal-info endpoint
    const { data } = await axiosInstance.get<ApiResponseData>(
      '/v1/patients/profile/personal'
    )
    console.log("data",{data})
    const api = data.data

    // Map the API response to PatientProfile interface
    // Build full_name from first_name, middle_name, last_name if full_name is not available
    const fullName = api.full_name || 
      [api.first_name, api.middle_name, api.last_name]
        .filter(Boolean)
        .join(' ') || ''

    const profile: PatientProfile = {
      id: api.id || '',
      full_name: fullName,
      first_name: api.first_name,
      middle_name: api.middle_name,
      last_name: api.last_name,
      email: api.email || '',
      contact_number: api.contact_number || '',
      phone_number: api.contact_number || '',
      phone_code: api.phone_code,
      emergency_contact_number: api.emergency_contact_number || '',
      family_contact_number: api.family_contact_number || '',
      date_of_birth: api.date_of_birth || '',
      blood_type: api.blood_type || '',
      marital_status: api.marital_status || '',
      occupation: api.occupation || '',
      preferred_language: api.preferred_language_name || '',
      preferred_language_id: api.preferred_language_id || '',
      gender: api.gender || '',
      address_line_1: api.address_line_1 || '',
      postal_code: api.postal_code || '',
      country: api.country_name || '',
      country_id: api.country_id || '',
      state: api.state_name || '',
      state_id: api.state_id || '',
      city: api.city_name || '',
      city_id: api.city_id || '',
      profile_img_url: api.avatar || '',
      avatar: api.avatar || ''
    }

    return profile
  } catch (error) {
    console.error('Error fetching patient profile:', error)
    throw error
  }
}

// Updated payload interface to match swagger exactly
export interface UpdatePatientProfilePayload {
  first_name?: string
  middle_name?: string
  last_name?: string
  date_of_birth?: string  // Changed from dob
  contact_number?: string  // Changed from phone_number
  gender?: string
  address_line_1?: string  // Changed from address
  postal_code?: string
  country_id?: string  // Changed from country
  state_id?: string  // Changed from state
  city_id?: string  // Changed from city
  avatar?: File  // Changed from profile_img
  blood_type?: string  // Changed from blood_group
  emergency_contact_number?: string  // Changed from emergency_number
  family_contact_number?: string
  occupation?: string
  marital_status?: string
  preferred_language_id?: string  // Changed from preferred_language
}

export const updatePatientProfile = async (payload: UpdatePatientProfilePayload) => {
  const formData = new FormData()

  // Append all fields according to swagger API specification
  if (payload.first_name !== undefined) formData.append('first_name', payload.first_name || '')
  if (payload.middle_name !== undefined) formData.append('middle_name', payload.middle_name || '')
  if (payload.last_name !== undefined) formData.append('last_name', payload.last_name || '')
  if (payload.date_of_birth !== undefined) formData.append('date_of_birth', payload.date_of_birth || '')
  if (payload.contact_number !== undefined) formData.append('contact_number', payload.contact_number || '')
  if (payload.gender !== undefined) formData.append('gender', payload.gender || '')
  if (payload.address_line_1 !== undefined) formData.append('address_line_1', payload.address_line_1 || '')
  if (payload.postal_code !== undefined) formData.append('postal_code', payload.postal_code || '')
  if (payload.country_id !== undefined) formData.append('country_id', payload.country_id || '')
  if (payload.state_id !== undefined) formData.append('state_id', payload.state_id || '')
  if (payload.city_id !== undefined) formData.append('city_id', payload.city_id || '')
  if (payload.blood_type !== undefined) formData.append('blood_type', payload.blood_type || '')
  if (payload.emergency_contact_number !== undefined) formData.append('emergency_contact_number', payload.emergency_contact_number || '')
  if (payload.family_contact_number !== undefined) formData.append('family_contact_number', payload.family_contact_number || '')
  if (payload.occupation !== undefined) formData.append('occupation', payload.occupation || '')
  if (payload.marital_status !== undefined) formData.append('marital_status', payload.marital_status || '')
  if (payload.preferred_language_id !== undefined) formData.append('preferred_language_id', payload.preferred_language_id || '')

  if (payload.avatar) {
    formData.append('avatar', payload.avatar)
  }

  // Use the personal-info endpoint for update
  const response = await axiosInstance.put('/v1/patients/profile/personal', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}