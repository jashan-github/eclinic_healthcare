import { setupInterceptors } from '@/config/axios-interceptors'
import axios from 'axios'

export type ApiResponse<T> = {
  data: T
  message: string
  status: boolean
}

// Create axios instance
const axiosInstance = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});


// Setting up interceptors
setupInterceptors(axiosInstance)

export default axiosInstance
