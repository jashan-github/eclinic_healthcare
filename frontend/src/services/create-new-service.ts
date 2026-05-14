// src/services/create-new-service.ts

import api from '@/lib/api'
import type { CreateServiceResponse } from './create-service'

export interface CreateNewServicePayload {
  service_name: string
  type: string // 'visit' or 'video'
  payment_method: string // 'pre_paid' or 'post-consultation'
  amount: string | number
  skip_price: boolean
  duration: string | number
  followup_validity?: string | number
  nickname?: string
  allow_patient_booking: boolean
  advance_booking_from?: number
  minimum_notice?: number
  appointment_type?: string // 'regular' or 'followup'
}

export interface CreatedServiceData {
  id: string
  doctor_id: string
  service_name: string
  type: string
  created_at: string
  updated_at: string
  [key: string]: any
}

export interface CreateNewServiceResponse {
  status: boolean
  message: string
  data: CreatedServiceData
}

export const createNewService = async (
  payload: CreateNewServicePayload
): Promise<CreatedServiceData> => {
  try {
    const response_id = await api.post<CreateServiceResponse>(
      '/v1/admin/service-types',
      {
        name: payload.service_name
      }
    )

    const appointment_treatment_id = response_id.data.data.id

    const formData = new FormData()

    formData.append('service_type_id', appointment_treatment_id)
    formData.append('name', payload.service_name)
    formData.append('type', payload.type) // visit or video
    formData.append('payment_method', payload.payment_method.replace('-', '_')) // pre_paid or post_consultation
    formData.append('duration', String(payload.duration))
    formData.append('appointment_type', payload.appointment_type || 'regular')

    formData.append('prefer_not_to_define_price', payload.skip_price ? '1' : '0')

    if (!payload.skip_price) {
      formData.append('amount', String(payload.amount))
    }

    formData.append('allow_patient_booking', payload.allow_patient_booking ? '1' : '0')
    formData.append('minimum_notice', String(payload.minimum_notice ?? 0))

    // Advance booking logic
    const hasAdvance = payload.advance_booking_from !== undefined && payload.advance_booking_from > 0
    formData.append('has_advance_booking', hasAdvance ? '1' : '0')
    if (hasAdvance) {
      formData.append('advance_booking_from', String(payload.advance_booking_from))
    }

    // Optional fields
    if (payload.nickname?.trim()) {
      formData.append('nickname', payload.nickname.trim())
    }
    

    if (payload.followup_validity) {
      formData.append('follow_up_validity', String(payload.followup_validity))
    }

    formData.append('description', payload.nickname?.trim() || payload.service_name)
    formData.append('status','1')
    
    // Final request
    const response = await api.post<CreateNewServiceResponse>(
      '/v1/admin/services',
      formData
    )

    return response.data.data
  } catch (error: any) {
    console.error('Failed to create new service:', error)

    const message =
      error?.response?.data?.message ||
      error?.response?.data?.errors?.[0] ||
      error?.message ||
      'Failed to create service'

    throw new Error(message)
  }
}