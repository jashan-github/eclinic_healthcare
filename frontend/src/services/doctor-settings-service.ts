// src/services/doctor-settings-service.ts

import api from '@/lib/api'

export interface StaffRestrictionsData {
  id?: string
  doctor_id?: string
  clinic_id: string
  access_all_patients_page: boolean
  ability_to_start_visit: boolean
  access_payment_page: boolean
  access_download_database: boolean
  created_at?: string
  updated_at?: string
}

export interface StaffRestrictionsResponse {
  status: boolean
  message: string
  data: StaffRestrictionsData
}

export interface FeeService {
  id: string
  service: string
  price: number
  status: boolean
  service_type: string | null
}

export type FeeServiceUpdate = Pick<FeeService, 'price' | 'status'>

// GET - Fetch current restrictions
export const fetchStaffRestrictions = async (): Promise<StaffRestrictionsData> => {
  try {
    const response = await api.get('/api/eclinic/v1/doctor/settings/staff-restrictions')
    return response.data.data
  } catch (error: any) {
    console.error('Failed to fetch staff restrictions:', error)
    throw new Error(error.response?.data?.message || 'Failed to load staff restrictions')
  }
}

// PUT - Update restrictions
export const updateStaffRestrictions = async (
  payload: Partial<StaffRestrictionsData>
): Promise<StaffRestrictionsData> => {
  try {
    const response = await api.put('/api/eclinic/v1/doctor/settings/staff-restrictions', payload)
    return response.data.data
  } catch (error: any) {
    console.error('Failed to update staff restrictions:', error)
    throw new Error(error.response?.data?.message || 'Failed to save staff restrictions')
  }
}

export const fetchFees = async (): Promise<FeeService[]> => {
  try {
    const response = await api.get('/api/eclinic/v1/doctor/settings/fees')
    return response.data.data
  } catch (error: any) {
    console.error('Failed to fetch fees:', error)
    throw new Error(error.response?.data?.message || 'Failed to load fees')
  }
}

export const updateFeeService = async (id: string, payload: FeeServiceUpdate): Promise<FeeService> => {
  try {
    const response = await api.put(`/api/eclinic/v1/doctor/settings/fees/${id}`, payload)
    return response.data.data
  } catch (error: any) {
    console.error('Failed to update fee:', error)
    throw new Error(error.response?.data?.message || 'Failed to update fee')
  }
}