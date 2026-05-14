import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { tokenCookies } from '@/utils/cookies'
import { refreshToken } from '@/features/auth/services/authentication-service'

/* ================= REQUEST ================= */
const onRequest = (config: InternalAxiosRequestConfig) => {
  const token = tokenCookies.getAccessToken()

  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
}

/* ================= REFRESH ================= */
const refreshAccessToken = async () => {
  const refreshTokenValue = tokenCookies.getRefreshToken()

  if (!refreshTokenValue) {
    throw new Error('No refresh token available')
  }

  const response = await refreshToken(refreshTokenValue)

  if (!response.success || !response.data) {
    throw new Error('Failed to refresh token')
  }

  const { access_token, refresh_token } = response.data

  // Tokens are already stored in cookies by the service/hook pattern
  // But since we're calling the service directly, we need to store them here
  tokenCookies.setAccessToken(access_token)
  tokenCookies.setRefreshToken(refresh_token)

  return access_token
}

/* ================= RESPONSE ================= */
let isRefreshing = false
let failedQueue: {
  resolve: (token: string) => void
  reject: (err: any) => void
}[] = []
let axiosInstanceRef: AxiosInstance | null = null

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(promise => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token!)
    }
  })
  failedQueue = []
}

const onResponseError = async (error: AxiosError) => {
  const originalRequest: any = error.config
  
  if (!error.response) {
  if (window.location.pathname.startsWith('/auth')) {
    return Promise.reject(error)
  }

  window.location.href = '/auth/login'
  return Promise.reject(error)
}


  if (error.response.status === 401 && !originalRequest._retry) {
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve((axiosInstanceRef || axios)(originalRequest))
          },
          reject,
        })
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      const newToken = await refreshAccessToken()
      processQueue(null, newToken)

      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return (axiosInstanceRef || axios)(originalRequest)
    } catch (err) {
      processQueue(err, null)
      tokenCookies.removeAllTokens()
      window.location.href = '/auth/login'
      return Promise.reject(err)
    } finally {
      isRefreshing = false
    }
  }

  return Promise.reject(error)
}


/* ================= SETUP ================= */
export const setupInterceptors = (axiosInstance: AxiosInstance) => {
  // Store reference to axios instance for use in interceptors
  axiosInstanceRef = axiosInstance
  axiosInstance.interceptors.request.use(onRequest)
  axiosInstance.interceptors.response.use(
    (response: AxiosResponse) => response,
    onResponseError
  )
}
