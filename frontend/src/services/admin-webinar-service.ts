// src/services/admin-webinar-service.ts
import api, { type ApiResponse } from '@/lib/api-webinars'
import type { UserRoleType } from '@/utils/user-role';

export interface AdminWebinarHost {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  role: UserRoleType;
}

export interface AdminWebinar {
  id: string
  title: string
  description: string
  webinar_date: string
  start_time: string
  end_time: string
  pricing_type: 'free' | 'paid'
  price: string
  participant_limit: number
  host_id: string
  host: AdminWebinarHost;
  created_by: string
  visibility: 'public' | 'private'
  agora_channel_name: string | null
  agora_token: string | null
  registered_count: number
  attended_count: number
  status?: 'draft' | 'scheduled' | 'live' | 'completed' | 'cancelled'
  agenda: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  currency?: string
}

export interface AdminWebinarsResponse {
  status: boolean
  message: string
  data: {
    webinars: AdminWebinar[]
  }
}

export interface AdminWebinarDetailResponse {
  status: boolean
  message: string
  data: {
    webinar: AdminWebinar
  }
}

export interface CreateWebinarPayload {
  title: string
  description: string
  webinar_date: string
  start_time: string
  end_time: string
  pricing_type: 'free' | 'paid'
  price?: number
  participant_limit: number
  host_id: string
  visibility: 'public' | 'private'
  agenda?: string
}

export interface UpdateWebinarPayload {
  title?: string
  description?: string
  webinar_date?: string
  start_time?: string
  end_time?: string
  pricing_type?: 'free' | 'paid'
  price?: number
  participant_limit?: number
  host_id?: string
  // status?: 'draft' | 'scheduled' | 'live' | 'completed' | 'cancelled'
  visibility?: 'public' | 'private'
  agenda?: string
}

// GET: Fetch all webinars
export const fetchAdminWebinars = async (): Promise<AdminWebinarsResponse> => {
  try {
    const response = await api.get<AdminWebinarsResponse>('/v1/admin/webinars')
    return response.data
  } catch (error) {
    console.error('Failed to fetch admin webinars:', error)
    throw new Error('Unable to load webinars')
  }
}

// GET: Fetch a specific webinar by ID
export const fetchAdminWebinarById = async (webinarId: string): Promise<AdminWebinarDetailResponse> => {
  try {
    const response = await api.get<AdminWebinarDetailResponse>(`/v1/admin/webinars/${webinarId}`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch webinar:', error)
    throw new Error('Unable to load webinar details')
  }
}

// POST: Create a new webinar
export const createAdminWebinar = async (payload: CreateWebinarPayload): Promise<AdminWebinar> => {
  try {
    const response = await api.post<ApiResponse<{ webinar: AdminWebinar }>>(
      '/v1/admin/webinars',
      payload
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to create webinar')
    }

    return response.data.data.webinar
  } catch (error: any) {
    console.error('Failed to create webinar:', error)
    throw new Error(error?.response?.data?.message || 'Unable to create webinar')
  }
}



// PUT: Update a webinar
export const updateAdminWebinar = async (
  webinarId: string,
  payload: UpdateWebinarPayload
): Promise<AdminWebinar> => {
  try {
    const response = await api.put<ApiResponse<{ webinar: AdminWebinar }>>(
      `/v1/admin/webinars/${webinarId}`,
      payload
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to update webinar')
    }

    return response.data.data.webinar
  } catch (error: any) {
    console.error('Failed to update webinar:', error)
    throw new Error(error?.response?.data?.message || 'Unable to update webinar')
  }
}

// DELETE: Delete a webinar
export const deleteAdminWebinar = async (webinarId: string): Promise<void> => {
  try {
    const response = await api.delete<ApiResponse<null>>(`/v1/admin/webinars/${webinarId}`)

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to delete webinar')
    }
  } catch (error: any) {
    console.error('Failed to delete webinar:', error)
    throw new Error(error?.response?.data?.message || 'Unable to delete webinar')
  }
}

