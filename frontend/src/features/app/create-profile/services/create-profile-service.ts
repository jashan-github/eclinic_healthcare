import axiosInstance from '@/lib/api'

export type CreateProfileData = {
  city_id?: string
  state_id?: string
  country_id?: string
  title?: string
  first_name: string
  middle_name?: string
  last_name: string
  gender?: string
  date_of_birth?: string
  country?: string
  state?: string
  city?: string
  phone_code?: string
  phone_number?: string
  address?: string
  postal_code?: string
}

export const createProfile = async (data: CreateProfileData) => {
  try {
    const response = await axiosInstance.post(
      '/v1/profile/complete',
      data,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  } catch (error) {
    console.log(error);
    throw error;
  }
}


