// src/services/doctors-service.ts
import type { ApiResponse } from "@/lib/api";
import axiosInstance from "@/lib/api";

export interface DoctorSearchFilters {
  specialty_id?: string;
  availability_day?: string;
  page?: number;
  limit?: number;
  shouldFetch?: boolean;
}

export interface DoctorService {
  id: string;
  name: string;
  nickname: string | null;
  service_mode: "IN_CLINIC" | "TELECLINIC";
  appointment_type: "REGULAR" | "FOLLOW_UP" | "EMERGENCY";
  slot_duration_minutes: number;
  price: number;
  currency: string;
}

export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  degrees: string[];
  rating: number | string;
  experience: number | string;
  consultationFee: number | string;
  total_fee: number;
  intakeFee: number;
  availability: string[];
  waiver_percent?: number;
  amount_before_waiver?: number;
  image: string;
  currency?: string;
  services: DoctorService[]; // ← New field
}

export interface DoctorsSearchResponse {
  doctors: Doctor[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

interface ApiPagination {
  current_page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

interface ApiDoctorService {
  id: string;
  name: string;
  nickname: string | null;
  service_mode: string;
  appointment_type: string;
  slot_duration_minutes: number;
  price: number;
  currency: string;
}

interface ApiDoctor {
  total_fee: number;
  id: string;
  name: string;
  specialty: string;
  qualifications: string;
  years_of_experience: number;
  lowest_consultation_fee: number;
  currency: string;
  rating: number;
  profile_image: string;
  available_days: string[];
  services: ApiDoctorService[]; // ← New field
}

interface ApiResponseData {
  doctors: ApiDoctor[];
  pagination: ApiPagination;
}

export const searchDoctors = async (
  filters?: DoctorSearchFilters,
): Promise<DoctorsSearchResponse> => {
  if (!filters?.shouldFetch) {
    throw new Error("Fetch not triggered");
  }

  try {
    const params = new URLSearchParams();

    if (filters.specialty_id) {
      params.append("specialty_id", filters.specialty_id);
    }

    if (filters.availability_day) {
      params.append("availability_day", filters.availability_day);
    }

    if (filters.page) {
      params.append("page", filters.page.toString());
    }

    params.append("limit", (filters.limit || 20).toString());

    const queryString = params.toString();
    const endpoint = `/v1/patient/doctors/search${queryString ? `?${queryString}` : ""}`;

    const { data } =
      await axiosInstance.get<ApiResponse<ApiResponseData>>(endpoint);

    const apiDoctors = data.data?.doctors || [];
    const pagination = data.data?.pagination || {
      current_page: 1,
      per_page: 20,
      total: 0,
      total_pages: 1,
    };

    const transformedDoctors: Doctor[] = apiDoctors.map((doc: ApiDoctor) => {
      const degrees = doc.qualifications
        ? doc.qualifications
            .split(",")
            .map((d) => d.trim())
            .filter(Boolean)
        : ["N/A"];

      const transformedServices: DoctorService[] = (doc.services || []).map(
        (service) => ({
          id: service.id,
          name: service.name,
          nickname: service.nickname,
          service_mode: service.service_mode as "IN_CLINIC" | "TELECLINIC",
          appointment_type: service.appointment_type as
            | "REGULAR"
            | "FOLLOW_UP"
            | "EMERGENCY",
          slot_duration_minutes: service.slot_duration_minutes,
          price: service.price,
          currency: service.currency,
        }),
      );

      return {
        id: doc.id,
        name: doc.name.startsWith("Dr.") ? doc.name : `Dr. ${doc.name}`,
        specialty: doc.specialty || "N/A",
        degrees,
        rating: doc.rating ? doc.rating : "N/A",
        experience: doc.years_of_experience || "N/A",
        consultationFee: doc.lowest_consultation_fee || "N/A",
        currency: doc.currency,
        intakeFee: 10,
        availability:
          doc.available_days.length > 0 ? doc.available_days : ["N/A"],
        image: doc.profile_image || "/assets/icons/doctor-icon.svg",
        services: transformedServices,
        total_fee: doc.total_fee,
      };
    });

    return {
      doctors: transformedDoctors,
      total: pagination.total,
      page: pagination.current_page,
      limit: pagination.per_page,
      totalPages: pagination.total_pages,
    };
  } catch (error) {
    console.error("Failed to search doctors:", error);
    throw error;
  }
};
