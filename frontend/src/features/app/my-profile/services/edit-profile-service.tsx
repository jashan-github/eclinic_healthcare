import api from "@/lib/api"

export interface UpdateProfilePayload {
  first_name: string
  middle_name: string
  last_name: string
  phone_number: string
  email: string
  dob: string
  years_of_experience: string
  education: string
  specializations: string[]
  languages: string[]
  about: string  // Changed from intro
  profile_img?: File
}

export const updateProfile = async (payload: UpdateProfilePayload) => {
  const formData = new FormData()

  formData.append('first_name', payload.first_name)
  formData.append('middle_name', payload.middle_name)
  formData.append('last_name', payload.last_name)
  formData.append('phone_number', payload.phone_number)
  formData.append('email', payload.email)
  formData.append('dob', payload.dob || '')
  formData.append('years_of_experience', payload.years_of_experience || '')
  formData.append('education', payload.education || '')
  formData.append('about', payload.about || '')  // Changed from intro

  // Send as comma-separated string, not JSON
  formData.append('specializations', payload.specializations.join(','))
  formData.append('languages', payload.languages.join(','))

  if (payload.profile_img) {
    formData.append('profile_img', payload.profile_img)
  }

  const response = await api.put('/v1/doctors/profile', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}