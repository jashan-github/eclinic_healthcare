import type { ApiResponse } from "@/lib/api";
import axiosInstance from "@/lib/api";

export interface AppointmentDoctorDetails {
  id: string;
  name: string;
  specialty: string;
  degrees: string[];
  rating: number | string;
  experience: number | string;
  consultationFee: number | string;
  intakeFee: number;
  availability: string[];
  image?: string;
  profile_img?: string;
  profile_image?: string;
  profile_img_url?: string;
  amount_before_waiver?: number;
  waiver_percent?: number;
  consultationTypes?: {
    teleconsultation: boolean;
    in_clinic: boolean;
  };
  total_fee: string;
  // Additional fields that might be in the API response
  [key: string]: any;
}

// API Response Type (adjust based on actual API response)
export interface ApiAppointmentDoctorDetails {
  id: string;
  name: string;
  profile_picture?: string;
  profile_image?: string;
  specialization?: string;
  specialty?: string;
  specializations?: Array<{
    id?: string;
    name?: string;
    [key: string]: any;
  }>;
  years_of_experience?: string | number;
  rating?: string | number;
  consultation_fee?: number;
  intake_fee?: number;
  total?: number;
  consultation_types?: {
    teleconsultation?: boolean;
    in_clinic?: boolean;
  };
  registration?: {
    experience?: string;
    year?: string;
    registration_no?: string;
    council?: string;
  };
  education?: Array<{
    degree?: string;
    university?: string;
    year?: string;
    [key: string]: any;
  }>;
  fee?: number | null;
  profile_img?: string;
  profile_img_url?: string;
  appointmentTypes?: {
    Visit?: boolean;
    Video?: boolean;
  };
  [key: string]: any;
}

export interface ConsultationType {
  mode: "IN_CLINIC" | "TELECONSULTATION";
  label: string;
  consultation_fee: number;
  intake_fee: number;
  total_fee: number;
  currency: string;
  is_available: boolean;
}

export interface ConsultationTypesResponse {
  consultation_types: ConsultationType[];
}

export interface TimeSlot {
  date: string;
  time: string;
  duration_minutes: number;
  consultation_mode: "IN_CLINIC" | "TELECONSULTATION";
  is_available: boolean;
}

export interface TimeSlotsResponse {
  time_slots: TimeSlot[];
}

export const getAppointmentDoctorDetails = async (
  doctorId: string,
  serviceId: string,
  date: string,
): Promise<AppointmentDoctorDetails> => {
  try {
    const { data } = await axiosInstance.get<
      ApiResponse<ApiAppointmentDoctorDetails>
    >(
      `/v1/patient/doctors/${doctorId}/summary?service_id=${serviceId}&date=${date}`,
    );

    const apiDoctor = data.data;

    // Transform API response to match our AppointmentDoctorDetails interface
    // Extract specialty - check specialization first (new API format), then specialty, then specializations array
    let specialty = "N/A";
    if (apiDoctor.specialization) {
      specialty = apiDoctor.specialization;
    } else if (apiDoctor.specialty) {
      specialty = apiDoctor.specialty;
    } else if (
      apiDoctor.specializations &&
      apiDoctor.specializations.length > 0
    ) {
      const firstSpec = apiDoctor.specializations[0];
      const specName = firstSpec.name || firstSpec.title || firstSpec.id;
      if (specName) {
        specialty = specName;
      }
    }

    // Extract degrees from education array
    let degrees: string[] = ["N/A"];
    if (apiDoctor.education && apiDoctor.education.length > 0) {
      const extractedDegrees = apiDoctor.education
        .map((edu: any) => {
          return (
            edu.degree ||
            edu.qualification ||
            edu.course ||
            edu.title ||
            (typeof edu === "string" ? edu : "")
          );
        })
        .filter((deg: any) => deg !== "" && deg !== null && deg !== undefined);

      if (extractedDegrees.length > 0) {
        degrees = extractedDegrees;
      }
    }

    // Parse experience - handle both "0 years" format and numeric format
    let experience: number | string = "N/A";
    // console.log("qwe",apiDoctor.years_of_experience)
    if (apiDoctor.years_of_experience) {
      const expStr = apiDoctor.years_of_experience.toString();
      // If it's already formatted like "0 years", use it as is
      if (expStr.includes("years") || expStr.includes("year")) {
        experience = expStr;
      } else {
        // Try to parse as number
        const parsedExp = parseInt(expStr);
        if (!isNaN(parsedExp)) {
          experience = parsedExp;
        }
      }
    } else if (apiDoctor.registration?.experience) {
      const parsedExp = parseInt(apiDoctor.registration.experience.toString());
      if (!isNaN(parsedExp) && parsedExp > 0) {
        experience = parsedExp;
      }
    }

    // Get consultation fee - check consultation_fee first (new API format), then fee
    const consultationFee: number | string =
      apiDoctor.consultation_fee !== null &&
      apiDoctor.consultation_fee !== undefined &&
      apiDoctor.consultation_fee > 0
        ? apiDoctor.consultation_fee
        : apiDoctor.fee !== null &&
            apiDoctor.fee !== undefined &&
            apiDoctor.fee > 0
          ? apiDoctor.fee
          : "N/A";

    // Get intake fee - check intake_fee first (new API format), otherwise default to 10
    const intakeFee =
      apiDoctor.intake_fee !== null && apiDoctor.intake_fee !== undefined
        ? apiDoctor.intake_fee
        : 10;

    // Rating - handle both formatted strings like "4.8/5" and numeric values
    let rating: number | string = "N/A";
    if (apiDoctor.rating !== null && apiDoctor.rating !== undefined) {
      if (typeof apiDoctor.rating === "string") {
        rating = apiDoctor.rating;
      } else if (typeof apiDoctor.rating === "number") {
        rating = apiDoctor.rating;
      }
    }

    // Derive availability from consultation_types (new API format) or appointmentTypes (old format)
    const availability: string[] = [];
    if (apiDoctor.consultation_types) {
      if (apiDoctor.consultation_types.in_clinic) {
        availability.push("Mon", "Tue", "Wed", "Thu", "Fri");
      }
      if (apiDoctor.consultation_types.teleconsultation) {
        availability.push("Mon", "Tue", "Wed", "Thu", "Fri", "Sat");
      }
    } else if (apiDoctor.appointmentTypes) {
      if (apiDoctor.appointmentTypes.Visit) {
        availability.push("Mon", "Tue", "Wed", "Thu", "Fri");
      }
      if (apiDoctor.appointmentTypes.Video) {
        availability.push("Mon", "Tue", "Wed", "Thu", "Fri", "Sat");
      }
    }
    if (availability.length === 0) {
      availability.push("N/A");
    }

    // Destructure properties we want to override from apiDoctor to avoid duplicates
    const {
      id,
      name,
      // specialization: apiSpecialization,
      // specialty: apiSpecialty,
      // fee,
      // consultation_fee: apiConsultationFee,
      // intake_fee: apiIntakeFee,
      // experience: apiExperience,
      // rating: apiRating,
      profile_picture,
      profile_img,
      profile_img_url,
      consultation_types: apiConsultationTypes,
      appointmentTypes: apiAppointmentTypes,
      total_fee,
      ...restApiDoctor
    } = apiDoctor;

    // Extract consultation types from API response
    let consultationTypes:
      | { teleconsultation: boolean; in_clinic: boolean }
      | undefined;
    if (apiConsultationTypes) {
      consultationTypes = {
        teleconsultation: apiConsultationTypes.teleconsultation === true,
        in_clinic: apiConsultationTypes.in_clinic === true,
      };
    } else if (apiAppointmentTypes) {
      consultationTypes = {
        teleconsultation: apiAppointmentTypes.Video === true,
        in_clinic: apiAppointmentTypes.Visit === true,
      };
    }

    // Clean name to remove duplicate "Dr." prefixes
    const cleanName = (nameStr: string): string => {
      if (!nameStr) return "N/A";
      // Remove duplicate "Dr." prefixes (case-insensitive)
      return nameStr.replace(/^(Dr\.?\s*)+/i, "Dr. ").trim();
    };

    return {
      id,
      name: cleanName(name || "N/A"),
      specialty,
      degrees,
      rating,
      experience,
      consultationFee,
      intakeFee,
      availability: [...new Set(availability)],
      image:
        profile_picture ||
        profile_img_url ||
        profile_img ||
        "/assets/icons/doctor-icon.svg",
      profile_img: profile_picture || profile_img,
      profile_img_url: profile_picture || profile_img_url,
      consultationTypes,
      total_fee,
      ...restApiDoctor,
    };
  } catch (error) {
    console.error("Failed to fetch appointment doctor details:", error);
    throw error;
  }
};

export const getConsultationTypes = async (
  doctorId: string,
  serviceId: string,
): Promise<ConsultationTypesResponse> => {
  try {
    const { data } = await axiosInstance.get<
      ApiResponse<ConsultationTypesResponse>
    >(
      `/v1/patient/doctors/${doctorId}/consultation-types?service_id=${serviceId}`,
    );

    return data.data;
  } catch (error) {
    console.error("Failed to fetch consultation types:", error);
    throw error;
  }
};

export const getTimeSlots = async (
  doctorId: string,
  serviceId: string,
  preferredDate: string,
  consultationMode: "IN_CLINIC" | "TELECONSULTATION",
): Promise<TimeSlotsResponse> => {
  try {
    const { data } = await axiosInstance.get<ApiResponse<TimeSlotsResponse>>(
      `/v1/patient/doctors/${doctorId}/time-slots`,
      {
        params: {
          service_id: serviceId,
          preferred_date: preferredDate,
          consultation_mode: consultationMode,
        },
      },
    );

    return data.data;
  } catch (error) {
    console.error("Failed to fetch time slots:", error);
    throw error;
  }
};

export interface TimeOffPeriod {
  id: string;
  doctor_id: string;
  clinic_id: string;
  start_datetime: string;
  end_datetime: string;
}

export interface TimeOffResponse {
  success: boolean;
  message: string;
  data: TimeOffPeriod[];
  errors: null | any;
  booking_window_days: number;
}

export interface TimeOffData {
  periods: TimeOffPeriod[];
  booking_window_days: number;
}

export const getDoctorTimeOff = async (
  doctorId: string,
): Promise<TimeOffData> => {
  try {
    const { data } = await axiosInstance.get<TimeOffResponse>(
      `/v1/patient/doctors/${doctorId}/time-off`,
    );

    return {
      periods: data.data || [],
      booking_window_days: data.booking_window_days || 30,
    };
  } catch (error) {
    console.error("Failed to fetch doctor time-off periods:", error);
    throw error;
  }
};
