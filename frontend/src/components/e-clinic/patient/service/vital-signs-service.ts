// src/services/vital-signs-service.ts
import api from '@/lib/api';

export interface VitalName {
  id: string;
  name: string;
  unit: string;
  display_order: string;
  is_active: boolean;
  data_type: 'number' | 'select' | 'text';
  options: string[] | null;
  max_entries_per_day: string;
  created_at: string;
  updated_at: string;
}

export interface VitalSignRecord {
  id: string;
  patient_id: string;
  vital_name_id: string;
  record_date: string;
  numeric_value: number | null;
  text_value: string | null;
  unit: string;
  notes: string | null;
  vital_name: {
    id: string;
    name: string;
    unit: string;
    data_type: 'number' | 'select' | 'text';
  };
}

export interface VitalSignsResponse {
  vital_signs: VitalSignRecord[];
  total: number;
  count: number;
}

export interface VitalNamesResponse {
  vital_names: VitalName[];
}

export interface VitalSignEntry {
  id: string | null;
  patient_id: string;
  vital_name_id: string;
  record_date: string | null;
  numeric_value: number | null;
  text_value: string | null;
  unit: string;
  notes: string | null;
  vital_name: {
    id: string;
    name: string;
    unit: string;
    data_type: 'number' | 'select' | 'text';
  };
}

export interface VitalHistoryResponse {
  vital_signs_by_date: Record<string, VitalSignEntry[]>;
  dates_count: number;
}

export const fetchVitalNames = async (): Promise<VitalName[]> => {
  try {
    const response = await api.get('/v1/patient-vital-signs/vital-names');
    const rawNames: VitalName[] = response.data.data.vital_names;

    return rawNames
      .filter((v) => v.is_active)
      .sort((a, b) => parseInt(a.display_order) - parseInt(b.display_order))
      .map((v) => ({
        ...v,
        options: v.options ? JSON.parse(v.options as any) : null,
      }));
  } catch (error) {
    console.error('Failed to fetch vital names:', error);
    throw new Error('Unable to load vital signs configuration');
  }
};

export const fetchPatientVitalSigns = async (
  patientId: string,
  offset: number = 0
): Promise<VitalSignsResponse> => {
  try {
    const response = await api.get(
      `/v1/patient-vital-signs/patient/${patientId}?offset=${offset}`
    );
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch patient vital signs:', error);
    throw new Error('Unable to load patient vital signs');
  }
};

export const saveVitalSigns = async (
  vitals: { vital_name_id: string; value: string | number }[],
  patientId?: string
) => {
  try {
    const payload = {
      vitals: vitals.map((v) => ({
        vital_name_id: v.vital_name_id,
        value: v.value,
      })),
    };

    if (patientId) {
      (payload as any).patient_id = patientId;
    }

    const response = await api.post('/v1/patient-vital-signs', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to save vital signs:', error);
    throw new Error('Failed to save vital signs');
  }
};

export const fetchPatientVitalHistory = async (patientId: string): Promise<VitalHistoryResponse> => {
  try {
    const response = await api.get(`/v1/patient-vital-signs/patient/${patientId}/history`);
    return response.data.data;
  } catch (error) {
    console.error('Failed to fetch patient vital history:', error);
    throw new Error('Unable to load historical vital signs');
  }
};

export const updateVitalSignsConsent = async (shareWithDoctor: boolean) => {
  try {
    const payload = {
      share_with_doctor: shareWithDoctor,
    };

    const response = await api.patch('/v1/patient-vital-signs/consent', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to update consent:', error);
    throw new Error('Unable to update consent');
  }
};