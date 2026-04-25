import api from "@/lib/api";

export interface AdminSettings {
  id: string;
  auto_approve_appointments: boolean;
  allow_same_day_booking: boolean;
  booking_window_days: number;
  created_at: string;
  updated_at: string;
}

export interface AdminSettingsResponse {
  success: boolean;
  message: string;
  errors: null | any;
  data: AdminSettings;
}

export interface UpdateAdminSettingsPayload {
  auto_approve_appointments?: boolean;
  allow_same_day_booking?: boolean;
  booking_window_days?: number;
}

export type UpdateNotificationSettingsPayload = Partial<{
  email_notify_password_reset: boolean;
  email_notify_appointment_accepted: boolean;
  email_notify_appointment_request: boolean;
}>;

export type UpdateWaiverSettingsPayload = {
  waiver_enabled: boolean;
  waiver_percent: number;
  waiver_doctor_decides: boolean;
};

// Get admin settings
export const fetchAdminSettings = async (): Promise<AdminSettingsResponse> => {
  try {
    const response = await api.get<AdminSettingsResponse>("/v1/admin/settings");
    return response.data;
  } catch (error) {
    console.error("Failed to fetch admin settings:", error);
    throw new Error("Unable to load admin settings. Please try again.");
  }
};

// Update admin settings
export const updateAdminSettings = async (
  payload: UpdateAdminSettingsPayload,
): Promise<AdminSettingsResponse> => {
  try {
    const response = await api.put<AdminSettingsResponse>(
      "/v1/admin/settings",
      payload,
    );
    return response.data;
  } catch (error) {
    console.error("Failed to update admin settings:", error);
    throw new Error("Unable to update admin settings. Please try again.");
  }
};

export const getNotificationSettings = async () => {
  try {
    const response = await api.get("/v1/admin/notification-settings");
    return response.data;
  } catch (error) {
    console.error("Failed to update admin settings:", error);
    throw new Error("Unable to Fetch the Notifaction Settings");
  }
};

export const updateNotificationSettings = async (
  payload: UpdateNotificationSettingsPayload,
) => {
  const response = await api.put("v1/admin/notification-settings", payload);
  return response.data;
};

export const getWaverNotificationSettings = async () => {
  try {
    const response = await api.get("/v1/admin/waiver-settings");
    return response.data;
  } catch (error) {
    console.error("Failed to update admin settings:", error);
    throw new Error("Unable to Fetch the Notifaction Settings");
  }
};

export const updateWaiverSettings = async (
  payload: UpdateWaiverSettingsPayload,
) => {
  const response = await api.put("v1/admin/waiver-settings", payload);
  return response.data;
};
