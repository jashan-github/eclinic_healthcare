import api, { type ApiResponse } from '@/lib/api'

export type AdminLoginResponse = {
  user: {
    id: string
    name: string
    email: string
    phone_code: string
    profile_img: string | null
    user_type: 'Administrator'
  }
  token: string
}

export type AdminLoginPayload = {
  email: string
  password: string
}

export const adminLogin = async (
  payload: AdminLoginPayload
): Promise<ApiResponse<AdminLoginResponse>> => {
  try {
    const { data } = await api.post<ApiResponse<AdminLoginResponse>>(
      '/api/eclinic/v1/admin/auth/login',
      payload
    )

    // Backend status check
    if (!data.status) {
      throw new Error(data.message || 'Admin login failed')
    }

    return data
  } catch (error: any) {
    console.error('[adminLogin] API Error:', error)

    // Extract message from backend if available
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Invalid email or password'

    throw new Error(message)
  }
}