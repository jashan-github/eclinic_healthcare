import axiosInstance from '@/lib/api'
import type { Profile } from '@/types/my-profile'

// New API Response Interface
interface ApiResponseData {
  status: boolean
  message: string
  data: {
    id: string
    user_id: string
    first_name: string | null
    middle_name: string | null
    last_name: string | null
    date_of_birth: string | null
    age: number
    phone_number: string
    email: string
    education: string | null
    years_of_experience: string | null
    languages: string[] | null
    specializations: string[] | null
    about: string | null
    profile_img: string | null
    created_at: string
    updated_at: string
  }
}

export const getMyProfileDetails = async (): Promise<Profile> => {
  try {
    const { data } = await axiosInstance.get<ApiResponseData>(
      '/v1/doctors/profile'
    )
    const api = data.data

    const profile: Profile = {
      id: api.id,
      name: api.first_name + ' ' + api.last_name || '',
      dob: api.date_of_birth || '',
      education: api.education || '',
      profile_img_url: api.profile_img || '',
      years_of_experience: api.years_of_experience || '',
      intro: api.about || '',
      about: api.about || '',
      languages: api.languages || [],
      specializations: api.specializations || [],
      email: api.email,
      phone_code: 91, // Default or from active_clinic if available
      phone_number: api.phone_number,
      first_name: api.first_name || '',
      middle_name: api.middle_name || '',
      last_name: api.last_name || '',
      full_name: `${api.first_name || ''} ${api.middle_name || ''} ${api.last_name || ''}`.trim(),
      fee: null,
      address: null,
      country: '',
      state: '',
      city: '',
      country_id: '',
      state_id: '',
      city_id: '',
      on_board_doctor: false,
      invite_code: '',
      invite_link: '',
      major_specialization: null,
      practice_areas: [],
      commonly_treats: [],
      facebook_link: null,
      linkedIn_link: null,
      instagram_link: null,
      youTube_link: null,
      active_clinic: null
    }

    return profile
  } catch (error) {
    console.error('Error fetching profile:', error)
    throw error
  }
}
