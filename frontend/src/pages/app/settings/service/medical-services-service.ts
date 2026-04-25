// src/services/medical-services-service.ts
import api from '@/lib/api';

// Raw response type from API
export interface MedicalServiceResponse {
  id: string;
  parent: string;
  name: string;
  image: string | null;
  status: boolean;
  created_at: string;
  updated_at: string;
}

interface ApiListResponse {
  success: boolean;
  message: string;
  data: {
    medical_services: MedicalServiceResponse[];
  };
}

interface ApiSingleResponse {
  success: boolean;
  message: string;
  data: {
    medical_service: MedicalServiceResponse;
  };
}

// GET all medical services
export async function getMedicalServices(status?: boolean): Promise<MedicalServiceResponse[]> {
  const params = status !== undefined ? { status: status.toString() } : {};
  const response = await api.get<ApiListResponse>('/v1/admin/medical-services', { params });
  return response.data.data.medical_services;
}

// GET single medical service
export async function getMedicalServiceById(id: string): Promise<MedicalServiceResponse> {
  const response = await api.get<ApiSingleResponse>(`/v1/admin/medical-services/${id}`);
  return response.data.data.medical_service;
}

// CREATE medical service
export async function createMedicalService(payload: {
  name: string;
  status: boolean;
}): Promise<MedicalServiceResponse> {
  const response = await api.post<ApiSingleResponse>('/v1/admin/medical-services', payload);
  return response.data.data.medical_service;
}

// UPDATE medical service
export async function updateMedicalService(id: string, payload: {
  name?: string;
  status?: boolean;
}): Promise<MedicalServiceResponse> {
  const response = await api.put<ApiSingleResponse>(`/v1/admin/medical-services/${id}`, payload);
  return response.data.data.medical_service;
}

// DELETE medical service
export async function deleteMedicalService(id: string): Promise<void> {
  await api.delete(`/v1/admin/medical-services/${id}`);
}
