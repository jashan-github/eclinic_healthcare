// src/services/patient-appointments-service.ts
import api from "@/lib/api";

export interface PatientAppointment {
  id: string;
  doctor_id: string;
  doctor_name: string;
  doctor_profile_image: string | null;
  specialty?: string | null; // For confirmed appointments
  doctor_specialty?: string | null; // For pending/accepted appointments
  service_id: string;
  service_name?: string | null;
  consultation_mode: "TELECONSULTATION" | "IN_CLINIC";
  // Confirmed appointments use these fields:
  appointment_date?: string;
  start_time?: string;
  end_time?: string;
  // Pending/Accepted appointments use these fields:
  preferred_date?: string;
  preferred_time?: string;
  status: "CONFIRMED" | "ACCEPTED" | "REJECTED" | "PENDING" | "CANCELLED";
  duration_minutes: number;
  price_amount: number;
  currency: string;
  reason?: string | null;
  has_reason?: boolean;
  payment_status: "pending" | "processing" | "paid" | "failed" | string;
  chat_room_id?: string | null;
  channel_name: string | null;
  session_id: string | null;
  amount_before_waiver?: number;
  waiver_percent?: number;
}

export interface GroupedAppointments {
  upcoming: PatientAppointment[];
  pending: PatientAppointment[];
  past: PatientAppointment[];
}

export const fetchGroupedAppointments =
  async (): Promise<GroupedAppointments> => {
    try {
      const response = await api.get("/v1/patient/appointments/grouped");
      return response.data.data;
    } catch (error) {
      console.error("Failed to fetch grouped appointments:", error);
      throw new Error("Unable to load appointments");
    }
  };
