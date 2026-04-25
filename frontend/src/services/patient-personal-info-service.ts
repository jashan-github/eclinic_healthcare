import type { ApiResponse } from '@/lib/api'
import axiosInstance from '@/lib/api'

export interface PatientPersonalInfo {
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
  state?: string
  city?: string
  zip_code?: string
  invite_code?: string
  [key: string]: any // Allow for additional fields from API
}

export const getPatientPersonalInfo = async (): Promise<PatientPersonalInfo> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<PatientPersonalInfo>>(
      '/v1/patients/profile/personal'
    )

    return data.data || {}
  } catch (error) {
    console.error('Error fetching patient personal info:', error)
    throw error
  }
}

export interface UpdatePatientPersonalInfoPayload {
  first_name?: string
  middle_name?: string
  last_name?: string
  dob?: string // Date of birth (format: YYYY-MM-DD)
  phone_code?: number
  phone_number?: string
  email?: string
  gender?: string
  address?: string
  postal_code?: string
  country?: string // UUID
  state?: string // UUID
  city?: string // UUID
  profile_img?: File
  blood_group?: string
  emergency_number?: string
  emergency_number_owner_name?: string
  family_contact_number?: string
  occupation?: string
  marital_status?: string
  preferred_language?: string
}

export const updatePatientPersonalInfo = async (payload: UpdatePatientPersonalInfoPayload) => {
  try {
    const formData = new FormData()

    // Required/Common fields
    if (payload.first_name !== undefined) formData.append('first_name', payload.first_name || '')
    if (payload.middle_name !== undefined) formData.append('middle_name', payload.middle_name || '')
    if (payload.last_name !== undefined) formData.append('last_name', payload.last_name || '')
    if (payload.dob !== undefined) formData.append('dob', payload.dob || '')
    if (payload.phone_code !== undefined) formData.append('phone_code', payload.phone_code?.toString() || '')
    if (payload.phone_number !== undefined) formData.append('phone_number', payload.phone_number || '')
    if (payload.email !== undefined) formData.append('email', payload.email || '')
    if (payload.gender !== undefined) formData.append('gender', payload.gender || '')
    if (payload.address !== undefined) formData.append('address', payload.address || '')
    if (payload.postal_code !== undefined) formData.append('postal_code', payload.postal_code || '')
    if (payload.country !== undefined) formData.append('country', payload.country || '')
    if (payload.state !== undefined) formData.append('state', payload.state || '')
    if (payload.city !== undefined) formData.append('city', payload.city || '')
    if (payload.blood_group !== undefined) formData.append('blood_group', payload.blood_group || '')
    if (payload.emergency_number !== undefined) formData.append('emergency_number', payload.emergency_number || '')
    if (payload.emergency_number_owner_name !== undefined) formData.append('emergency_number_owner_name', payload.emergency_number_owner_name || '')
    if (payload.family_contact_number !== undefined) formData.append('family_contact_number', payload.family_contact_number || '')
    if (payload.occupation !== undefined) formData.append('occupation', payload.occupation || '')
    if (payload.marital_status !== undefined) formData.append('marital_status', payload.marital_status || '')
    if (payload.preferred_language !== undefined) formData.append('preferred_language', payload.preferred_language || '')

    if (payload.profile_img) {
      formData.append('profile_img', payload.profile_img)
    }

    const { data } = await axiosInstance.post<ApiResponse<PatientPersonalInfo>>(
      '/api/eclinic/v1/patient/profile/update-personal-info',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return data.data
  } catch (error) {
    console.error('Error updating patient personal info:', error)
    throw error
  }
}

