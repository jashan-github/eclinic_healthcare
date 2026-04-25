// src/services/webinar-service.ts
import api from '@/lib/api-webinars'
import type { UserRoleType } from '@/utils/user-role';

export interface AdminWebinarHost {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  role: UserRoleType;
}
export interface DoctorWebinar {
  id: string
  title: string
  description: string
  webinar_date: string
  start_time: string
  end_time: string
  pricing_type: 'free' | 'paid'
  host: AdminWebinarHost;
  price: number
  participant_limit: number
  host_id: string
  created_by: string
  status: 'scheduled' | 'live' | 'completed' | 'cancelled'
  visibility: 'public' | 'private'
  agora_channel_name: string | null
  agora_token: string | null
  registered_count: number
  attended_count: number
  agenda: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  is_registered?: boolean
  can_join?: boolean
}

export interface WebinarResponse {
  status: boolean
  message: string
  data: {
    webinars: DoctorWebinar[]
  }
}

// Get all upcoming webinars for doctor
export const fetchDoctorWebinars = async (): Promise<WebinarResponse> => {
  try {
    const response = await api.get<WebinarResponse>('/v1/doctor/webinars')
    return response.data
  } catch (error) {
    console.error('Failed to fetch doctor webinars:', error)
    throw new Error('Unable to load webinars. Please try again.')
  }
}

