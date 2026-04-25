// src/services/rx-template-service.ts
import api from '@/lib/api'

export interface RxTemplate {
  id: string
  doctor_id: string
  clinic_location_id: string
  clinic_location_name: string
  letterhead_image_path: string | null
  letterhead_image_url: string | null
  template_name: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface RxTemplateResponse {
  status: boolean
  message: string
  data: {
    templates: RxTemplate[]
  }
}

export interface SaveRxTemplatePayload {
  clinic_location_id: string
  template_name?: string
  letterhead?: File
  use_default_letterhead: boolean
}

// Fetch existing template(s)
// If clinicLocationId is provided, filter by that location
// If not provided, fetch all templates for the doctor
export const fetchRxTemplate = async (clinicLocationId?: string): Promise<RxTemplateResponse> => {
  const params = clinicLocationId ? { clinic_location_id: clinicLocationId } : {}
  const response = await api.get(`/v1/doctor/rx-templates`, { params })
  return response.data
}

// Save/Create template
export const saveRxTemplate = async (payload: SaveRxTemplatePayload) => {
  const formData = new FormData()

  formData.append('clinic_location_id', payload.clinic_location_id)
  
  if (payload.template_name) {
    formData.append('template_name', payload.template_name)
  }
  
  formData.append('use_default_letterhead', payload.use_default_letterhead ? 'true' : 'false')
  
  if (!payload.use_default_letterhead && payload.letterhead) {
    formData.append('letterhead', payload.letterhead)
  }

  const response = await api.post('/v1/doctor/rx-templates', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

// Update existing template by ID
export const updateRxTemplate = async (templateId: string, payload: SaveRxTemplatePayload) => {
  const formData = new FormData()

  formData.append('clinic_location_id', payload.clinic_location_id)
  
  if (payload.template_name) {
    formData.append('template_name', payload.template_name)
  }
  
  formData.append('use_default_letterhead', payload.use_default_letterhead ? 'true' : 'false')
  
  if (!payload.use_default_letterhead && payload.letterhead) {
    formData.append('letterhead', payload.letterhead)
  }

  const response = await api.put(`/v1/doctor/rx-templates/${templateId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}