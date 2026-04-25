// src/services/admin-vitals-service.ts
import api from '@/lib/api';

// Raw response type from API
export interface VitalResponse {
  id: string;
  name: string;
  unit: string;
  display_order: string;
  is_active: boolean;
  data_type: string;
  options: string | null; // JSON string like "["Oral","Axillary"]"
  max_entries_per_day: string;
  created_at: string;
  updated_at: string;
}

interface ApiListResponse {
  success: boolean;
  message: string;
  data: {
    vital_names: VitalResponse[];
  };
}

interface ApiSingleResponse {
  success: boolean;
  message: string;
  data: VitalResponse;
}

// GET all vitals
// src/services/admin-vitals-service.ts
export async function getVitals(): Promise<VitalResponse[]> {
  const response = await api.get<ApiListResponse>('/v1/admin/vital-names');
  return response.data.data.vital_names
    .sort((a, b) => Number(a.display_order) - Number(b.display_order));
}

// GET single vital
export async function getVitalById(id: string): Promise<VitalResponse> {
  const response = await api.get<ApiSingleResponse>(`/v1/admin/vital-names/${id}`);
  return response.data.data;
}

// CREATE vital
export async function createVital(payload: {
  name: string;
  unit?: string;
  data_type: string;
  is_active?: boolean;
  options?: string[] | null;
  max_entries_per_day?: string;
}): Promise<VitalResponse> {
  const response = await api.post<ApiSingleResponse>('/v1/admin/vital-names', {
    ...payload,
    options: payload.options ? JSON.stringify(payload.options) : null,
  });
  return response.data.data;
}

export async function updateVital(id: string, payload: {
  name: string;
  unit?: string;
  data_type: string;
  is_active?: boolean;
  options?: string[] | null;
  max_entries_per_day?: string;
}): Promise<VitalResponse> {
  const response = await api.patch<ApiSingleResponse>(`/v1/admin/vital-names/${id}`, {
    ...payload,
    options: payload.options ? JSON.stringify(payload.options) : null,
  });
  return response.data.data;
}

// DELETE vital
export async function deleteVital(id: string): Promise<void> {
  await api.delete(`/v1/admin/vital-names/${id}`);
}

// REORDER vitals (display_order update)
export async function reorderVitals(orderedVitals: VitalResponse[]): Promise<void> {
  const updates = orderedVitals.map((vital, index) => ({
    id: vital.id,
    display_order: String(index + 1), // 1-based indexing
  }));

  for (const { id, display_order } of updates) {
    await api.patch(`/v1/admin/vital-names/${id}`, { display_order });
  }
}