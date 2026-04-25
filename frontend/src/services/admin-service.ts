// src/services/admin-service.ts
import api from "@/lib/api";

// ==================== Interfaces ====================

export interface AdminService {
  id: string;
  clinic_id: string;
  name: string;
  nickname?: string | null;
  service_mode: string;
  appointment_type: string;
  is_bookable: boolean;
  advance_booking_days: number;
  minimum_notice_minutes: number;
  payment_type: string;
  price: number;
  base_price?: number;
  currency?: string;
  created_by?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MappedService {
  id: string;
  serviceName: string;
  price: number;
  type: string;
  status: "Active" | "Inactive";
  currency?: string;
}

export interface CreateAdminServicePayload {
  advance_booking_days: number;
  appointment_type: "REGULAR" | "FOLLOWUP";
  clinic_id: string;
  is_bookable: boolean;
  minimum_notice_minutes: number;
  name: string;
  nickname?: string;
  payment_type: "PREPAID" | "POSTPAID";
  price: number;
  service_mode: "IN_CLINIC" | "TELECONSULTATION";
}

export interface CreatedAdminServiceData {
  id: string;
  name: string;
  clinic_id: string;
  created_at: string;
  updated_at: string;
  [key: string]: any;
}

export interface CreateAdminServiceResponse {
  status: boolean;
  message: string;
  data: CreatedAdminServiceData;
}

export interface UpdateServicePayload {
  type: "visit" | "video";
  payment_method: "pre-paid" | "post_consultation";
  amount: string | number;
  prefer_not_to_define_price: number;
  duration: string | number;
  follow_up_validity?: string | number;
  nickname?: string;
  allow_patient_booking: number;
  advance_booking_from: number;
  minimum_notice: number;
  has_advance_booking: number;
  appointment_type?: "REGULAR" | "FOLLOW_UP";
  description?: string;
  appointment_treatment_id?: string;
}

export interface UpdatedServiceData {
  id: string;
  service_name: string;
  nickname: string | null;
  doctor_id: string;
  type: string;
  amount: number;
  payment_method: string | null;
  duration: number;
  follow_up_validity: number | null;
  allow_patient_booking: number;
  advance_booking_from: number;
  minimum_notice: number | null;
  description: string;
  appointment_type: string | null;
  created_at: string;
  updated_at: string;
}

// ==================== Service Functions ====================

// Get all services
export const fetchServices = async (): Promise<MappedService[]> => {
  try {
    const response = await api.get(`/v1/admin/services`);

    // Backend response: { success: true, message: "...", data: [...] }
    const responseData = response.data?.data || response.data || [];
    const rawServices: AdminService[] = Array.isArray(responseData)
      ? responseData
      : [];

    if (!Array.isArray(rawServices)) {
      console.error("Expected array but got:", typeof rawServices, rawServices);
      return [];
    }

    return rawServices
      .filter((item) => item && item.id) // Filter out any invalid items
      .map((item) => {
        const name = item.name || item.nickname || "Unnamed Service";
        return {
          id: item.id || "",
          serviceName: String(name || "Unnamed Service"),
          price: item.price,
          type:
            item.service_mode === "IN_CLINIC"
              ? "In-Clinic"
              : item.service_mode === "TELECONSULTATION"
                ? "Teleconsultation"
                : item.service_mode || "N/A",
          status: item.is_bookable === true ? "Active" : "Inactive",
          currency: item.currency,
        };
      });
  } catch (error) {
    console.error("Failed to fetch services:", error);
    throw new Error("Unable to load services data");
  }
};

// Get service by ID
export const getServiceById = async (
  serviceId: string,
): Promise<AdminService> => {
  try {
    const response = await api.get(`/v1/admin/services/${serviceId}`);
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch service:", error);
    throw new Error("Unable to load service data");
  }
};

// Create service
export const createAdminService = async (
  payload: CreateAdminServicePayload,
): Promise<CreatedAdminServiceData> => {
  try {
    const response = await api.post<CreateAdminServiceResponse>(
      "/v1/admin/services",
      payload,
    );

    return response.data.data;
  } catch (error: any) {
    console.error("Failed to create admin service:", error);

    const message =
      error?.response?.data?.message ||
      error?.response?.data?.errors?.[0] ||
      error?.message ||
      "Failed to create service";

    throw new Error(message);
  }
};

// Update service
export const updateService = async (
  serviceId: string,
  payload: UpdateServicePayload,
  clinicId?: string,
  serviceName?: string,
): Promise<UpdatedServiceData> => {
  try {
    // Check if user is admin - if so, use JSON payload structure matching create service
    const userRole = localStorage.getItem("role");
    const isAdmin = userRole === "super_admin" || userRole === "clinic_admin";

    if (isAdmin) {
      // For admin, transform payload to match create service structure
      const adminPayload: {
        name?: string;
        nickname?: string;
        service_mode?: "IN_CLINIC" | "TELECONSULTATION";
        appointment_type?: "REGULAR" | "FOLLOWUP";
        payment_type?: "PREPAID" | "POSTPAID";
        price?: number;
        is_bookable?: boolean;
        advance_booking_days?: number;
        minimum_notice_minutes?: number;
        clinic_id?: string;
      } = {};

      // Add service name if provided (for updates)
      if (serviceName) {
        adminPayload.name = serviceName;
      }

      // Map type to service_mode
      if (payload.type) {
        adminPayload.service_mode =
          payload.type === "video" ? "TELECONSULTATION" : "IN_CLINIC";
      }

      // Map payment_method to payment_type
      if (payload.payment_method) {
        adminPayload.payment_type =
          payload.payment_method === "pre-paid" ? "PREPAID" : "POSTPAID";
      }

      // Map appointment_type
      if (payload.appointment_type) {
        adminPayload.appointment_type =
          payload.appointment_type === "FOLLOW_UP" ? "FOLLOWUP" : "REGULAR";
      }

      // Map price
      if (
        payload.amount !== undefined &&
        payload.amount !== "" &&
        !payload.prefer_not_to_define_price
      ) {
        adminPayload.price =
          typeof payload.amount === "string"
            ? parseFloat(payload.amount)
            : payload.amount;
      }

      // Map is_bookable
      if (payload.allow_patient_booking !== undefined) {
        adminPayload.is_bookable = payload.allow_patient_booking === 1;
      }

      // Map advance_booking_days
      if (payload.advance_booking_from !== undefined) {
        adminPayload.advance_booking_days = payload.advance_booking_from;
      }

      // Map minimum_notice_minutes (convert hours to minutes)
      if (payload.minimum_notice !== undefined) {
        adminPayload.minimum_notice_minutes = payload.minimum_notice * 60;
      }

      // Add optional fields
      if (payload.nickname) {
        adminPayload.nickname = payload.nickname;
      }

      // Add clinic_id if provided
      if (clinicId) {
        adminPayload.clinic_id = clinicId;
      }

      const response = await api.patch<{
        status: boolean;
        message: string;
        data: UpdatedServiceData;
      }>(`/v1/admin/services/${serviceId}`, adminPayload);

      return response.data.data;
    } else {
      // For doctor, use FormData (original implementation)
      const formData = new FormData();

      // Append all fields as string (backend expects FormData)
      Object.entries(payload).forEach(([key, value]) => {
        if (value === null || value === undefined) return;
        formData.append(key, value.toString());
      });

      const response = await api.patch<{
        status: boolean;
        message: string;
        data: UpdatedServiceData;
      }>(`/v1/admin/services/${serviceId}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return response.data.data;
    }
  } catch (error: any) {
    console.error("Failed to update service:", error);
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.errors?.[0] ||
      error?.message ||
      "Failed to update service";
    throw new Error(message);
  }
};

// Delete service
export const deleteService = async (serviceId: string): Promise<void> => {
  try {
    await api.delete(`/v1/admin/services/${serviceId}`);
  } catch (error) {
    console.error("Failed to delete service:", error);
    throw new Error("Unable to delete service");
  }
};
