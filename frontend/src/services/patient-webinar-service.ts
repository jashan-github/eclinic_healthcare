import api from "@/lib/api-webinars";
import type { UserRoleType } from "@/utils/user-role";

export interface AdminWebinarHost {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  role: UserRoleType;
  speciality?: string;
}

export interface PatientWebinar {
  id: string;
  title: string;
  description: string;
  webinar_date: string; // YYYY-MM-DD
  start_time: string; // HH:MM:SS
  end_time: string; // HH:MM:SS
  pricing_type: "free" | "paid";
  price: string;
  participant_limit: number;
  host_id: string;
  host: AdminWebinarHost;
  host_name?: string;
  host_specialty?: string;
  host_image?: string;
  host_experience?: string;
  status: "scheduled" | "live" | "completed" | "cancelled";
  visibility: "public" | "private";
  registered_count: number;
  attended_count: number;
  agenda: string;
  created_at: string;
  updated_at: string;
  currency?: string;
  is_registered: boolean;
  can_join: boolean;
}

export interface PatientWebinarsResponse {
  success: boolean;
  message: string;
  data: {
    webinars: PatientWebinar[];
  };
}

/**
 * Get upcoming webinars for patients
 */
export const fetchPatientWebinars =
  async (): Promise<PatientWebinarsResponse> => {
    try {
      const response = await api.get<PatientWebinarsResponse>(
        "/v1/patient/webinars",
      );
      console.log("📡 Patient webinars response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch patient webinars:", error);
      throw new Error("Unable to load webinars. Please try again.");
    }
  };
