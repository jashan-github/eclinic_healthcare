import api from '@/lib/api'

export interface AdminDoctor {
  id: string
  name: string
  email: string
  phone?: string | null
  is_active: boolean
  [key: string]: any
}

export interface AdminDoctorsResponse {
  success: boolean
  message: string
  data: {
    doctors: AdminDoctor[]
    pagination?: {
      total: number
      page: number
      per_page: number
      total_pages: number
    }
  }
  errors: null | any
}

export const fetchAdminDoctors = async (isActive: boolean = true): Promise<AdminDoctor[]> => {
  try {
    const response = await api.get<AdminDoctorsResponse>('/v1/admin/doctors', {
      params: {
        is_active: isActive
      }
    })
    
    return response.data.data?.doctors || []
  } catch (error) {
    console.error('Failed to fetch admin doctors:', error)
    throw new Error('Unable to load doctors data')
  }
}
