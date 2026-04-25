import api from '@/lib/api'
import axios from 'axios'
import type { UserRoleType } from '@/utils/user-role'

const LOGIN_ENDPOINT = '/v1/auth/login'

// Create a separate axios instance for refresh token to avoid interceptor loops
const refreshApi = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create a separate axios instance for login with longer timeout
const loginApi = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api',
  timeout: 30000, // 30 seconds for login requests
  headers: {
    'Content-Type': 'application/json',
  },
})

export type LoginPayload = {
  email?: string
  username?: string
  password: string
  role?: string
}

export type LoginUser = {
  id: string
  email: string
  name: string
  phone: string | null
  role: UserRoleType
  clinic_id: string | null
  is_active: boolean
  is_verified: boolean
  is_profile_complete: boolean
  email_verified_at: string | null
  created_at: string
  updated_at: string
  last_login_at: string | null
  avatar: string | null
}

export type LoginResponse = {
  user: LoginUser
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  is_profile_complete: boolean
}

export type NewApiResponse<T> = {
  success: boolean
  message: string
  data: T
  errors: any | null
}

// Optional: Mock for development
export const MOCK_LOGIN_RESPONSE: NewApiResponse<LoginResponse> = {
  success: true,
  message: 'Login successful',
  data: {
    user: {
      id: '549ea270-45d8-4fda-a2a9-f8e5c582f612',
      email: 'dr.bajwa@gmail.com',
      name: 'NS Bajwa',
      phone: '+1234567891',
      role: 'doctor',
      clinic_id: 'db9b729d-a591-4543-9265-a0e6ed4f1025',
      is_active: true,
      is_verified: false,
      email_verified_at: null,
      created_at: '2025-12-24T08:01:32.447624+00:00',
      updated_at: '2025-12-24T09:33:29.624088+00:00',
      last_login_at: '2025-12-24T09:33:29.945908+00:00',
      avatar: null,
      is_profile_complete: true
    },
    access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...', // truncated
    refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...', // truncated
    token_type: 'bearer',
    expires_in: 1800,
    is_profile_complete: false
  },
  errors: null
}

export const loginUser = async (
  payload: LoginPayload
): Promise<NewApiResponse<LoginResponse>> => {
  try {
    // console.log('[loginUser] POST →', LOGIN_ENDPOINT, payload)

    // Use loginApi with longer timeout (30 seconds) for login requests
    const { data } = await loginApi.post<NewApiResponse<LoginResponse>>(
      LOGIN_ENDPOINT,
      payload
    )

    return data

    // return MOCK_LOGIN_RESPONSE // uncomment for mock
  } catch (error: any) {
    console.error('[loginUser] Error:', error)
    
    // Handle timeout errors with better message
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const timeoutError = new Error('Request timeout. The server is taking too long to respond. Please check your connection and try again.')
      ;(timeoutError as any).response = error.response
      ;(timeoutError as any).code = error.code
      throw timeoutError
    }
    
    throw error
  }
}

const REFRESH_TOKEN_ENDPOINT = '/v1/auth/refresh'

export type RefreshTokenPayload = {
  refresh_token: string
}

export type RefreshTokenResponse = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export const refreshToken = async (
  refreshTokenValue: string
): Promise<NewApiResponse<RefreshTokenResponse>> => {
  try {
    // Use refreshApi (without interceptors) to avoid infinite loop
    const { data } = await refreshApi.post<NewApiResponse<RefreshTokenResponse>>(
      REFRESH_TOKEN_ENDPOINT,
      {
        refresh_token: refreshTokenValue,
      }
    )

    return data
  } catch (error: any) {
    console.error('[refreshToken] Error:', error)
    throw error
  }
}

const SIGNUP_ENDPOINT = '/v1/auth/register'

export type SignupPayload = {
  title: string
  first_name: string
  middle_name?: string
  last_name: string
  date_of_birth: string
  gender: 'Male' | 'Female' | 'Other'
  phone_code: string
  phone_number: string
  email: string
  password: string
  password_confirmation: string
  clinic_id?: string
  role: string
  country_id: string
}

export type SignupResponse = {
  user: LoginUser
  token: string
  refresh_token?: string
}

export type SignupApiResponse = {
  success: boolean
  message: string
  status: boolean
  data: SignupResponse
  errors: any | null
}

export const signupUser = async (
  payload: SignupPayload
): Promise<SignupApiResponse> => {
  try {
    const { data } = await api.post<SignupApiResponse>(
      SIGNUP_ENDPOINT,
      payload
    )

    return data
  } catch (error: any) {
    console.error('[signupUser] Error:', error)
    throw error
  }
}

const LOGOUT_ENDPOINT = '/v1/auth/logout'

export type LogoutResponse = {
  success: boolean
  message: string
}

export const logoutUser = async (): Promise<LogoutResponse> => {
  try {
    const { data } = await api.post<LogoutResponse>(
      LOGOUT_ENDPOINT,
      {}
    )

    return data
  } catch (error: any) {
    console.error('[logoutUser] Error:', error)
    throw error
  }
}