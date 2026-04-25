// src/services/create-service.ts
import api from '@/lib/api'

export interface CreateServicePayload {
    name: string
}

export interface CreatedServiceData {
    id: string
    doctor_id: string
    service_name: string
    type: string
    created_at: string
    updated_at: string
}

export interface CreateServiceResponse {
    status: boolean
    message: string
    data: CreatedServiceData
}

export const createService = async (
    payload: CreateServicePayload
): Promise<CreatedServiceData> => {
    try {
        const response = await api.post<CreateServiceResponse>('/api/eclinic/v1/doctor/availability/service-types', {
            service_name: payload.name
        })

        return response.data.data
    } catch (error: any) {
        console.error('Failed to create service:', error)

        const message =
            error?.response?.data?.message ||
            error?.response?.data?.error ||
            error?.message ||
            'Failed to create service'

        throw new Error(message)
    }
}