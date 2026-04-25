// src/services/appointment-service.ts
import api from "@/lib/api";

export interface PaginationInfo {
  current_page: number;
  per_page: number;
  total: number;
  last_page: number;
  from: number;
  to: number;
}

export interface PaginatedAppointments {
  data: AppointmentItem[];
  current_page: number;
  per_page: number;
  total: number;
  last_page: number;
  from: number;
  to: number;
}

export interface AppointmentResponse {
  success: boolean;
  message: string;
  data: {
    today: PaginatedAppointments;
    upcoming: PaginatedAppointments;
    completed: PaginatedAppointments;
  };
  errors: any;
}

export interface AppointmentItem {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_profile_image: string | null;
  patient_gender: string;
  patient_age: number;
  service_id: string;
  service_name: string;
  consultation_mode: "IN_CLINIC" | "TELECONSULTATION";
  appointment_date: string;
  start_time: string;
  end_time: string;
  status: "CONFIRMED" | "PENDING" | "ACCEPTED" | "REJECTED" | "CANCELLED";
  price_amount: number;
  currency: string;
  duration_minutes: number;
  payment_type?: string;
  is_appointment_request?: boolean;
  appointment_request_id?: string | null;
  session_id?: string | null;
  amount_before_waiver?: number;
  waiver_percent?: number;
}

export interface DoctorAppointmentsParams {
  today_page?: number;
  upcoming_page?: number;
  completed_page?: number;
  per_page?: number;
}

export const fetchDoctorAppointments = async (
  params?: DoctorAppointmentsParams,
): Promise<AppointmentResponse["data"]> => {
  try {
    const queryParams: Record<string, string> = {};

    if (params?.today_page) {
      queryParams.today_page = String(params.today_page);
    }
    if (params?.upcoming_page) {
      queryParams.upcoming_page = String(params.upcoming_page);
    }
    if (params?.completed_page) {
      queryParams.completed_page = String(params.completed_page);
    }
    if (params?.per_page) {
      queryParams.per_page = String(params.per_page);
    }

    const response = await api.get<AppointmentResponse>(
      "v1/doctor/appointments/grouped",
      {
        params: queryParams,
      },
    );

    return response.data.data;
  } catch (error: any) {
    console.error("Failed to fetch doctor appointments:", error);
    throw new Error(
      error.response?.data?.message || "Unable to load appointments",
    );
  }
};

export const cancelAppointment = async (
  appointmentId: string,
): Promise<any> => {
  const response = await api.post(`/appointments/${appointmentId}/cancel`);
  return response.data;
};

export const startTeleconsultation = async (
  appointmentId: string,
): Promise<any> => {
  const response = await api.post(`/appointments/${appointmentId}/start-call`);
  return response.data;
};
