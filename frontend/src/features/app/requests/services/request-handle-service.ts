// src/services/request-handle-service.ts

import api from "@/lib/api";

export interface AcceptRequestResponse {
  success: boolean;
  message: string;
  data: {
    id: string;
    doctor_id: string;
    patient_id: string;
    service_id: string;
    clinic_id: string;
    preferred_date: string;
    preferred_time: string;
    consultation_mode: string;
    duration_minutes: number;
    status: string;
    price_amount: number;
    currency: string;
    pricing_source: string;
    rejection_reason: string;
    created_at: string;
    updated_at: string;
  };
  errors: any;
}

export interface RejectRequestPayload {
  rejection_reason: string;
}

export interface AcceptRequestPayload {
  waiver_percent?: number;
}

export interface DoctorWaiverSettings {
  waiver_enabled: boolean;
  waiver_doctor_decides: boolean;
  waiver_choices: number[];
}

export interface DoctorWaiverSettingsResponse {
  success: boolean;
  message: string;
  data: DoctorWaiverSettings;
  errors: any;
}

export const getDoctorWaiverSettings =
  async (): Promise<DoctorWaiverSettingsResponse> => {
    const response = await api.get<DoctorWaiverSettingsResponse>(
      "/v1/appointment/requests/waiver-settings",
    );
    return response.data;
  };

export const acceptRequest = async (
  requestId: string,
  payload?: AcceptRequestPayload,
): Promise<AcceptRequestResponse> => {
  const response = await api.post<AcceptRequestResponse>(
    `/v1/appointment/requests/${requestId}/accept`,
    payload,
  );
  return response.data;
};

export const rejectRequest = async (
  requestId: string,
  payload: RejectRequestPayload,
): Promise<AcceptRequestResponse> => {
  try {
    const response = await api.post<AcceptRequestResponse>(
      `/v1/appointment/requests/${requestId}/reject`,
      payload,
    );
    return response.data;
  } catch (error) {
    console.error("Failed to reject request:", error);
    throw new Error("Unable to reject request");
  }
};
