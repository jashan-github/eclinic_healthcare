import { useQuery } from "@tanstack/react-query";
import {
  getAppointmentDoctorDetails,
  getConsultationTypes,
  getTimeSlots,
  getDoctorTimeOff,
  type AppointmentDoctorDetails,
  type ConsultationTypesResponse,
  type TimeSlotsResponse,
  type TimeOffData,
} from "@/services/appointment-doctor-details-service";

export const useAppointmentDoctorDetails = (
  doctorId: string | null,
  serviceId: string,
  date: string,
) => {
  return useQuery<AppointmentDoctorDetails, Error>({
    queryKey: ["appointmentDoctorDetails", doctorId, serviceId, date],
    queryFn: () => {
      if (!doctorId) {
        throw new Error("Doctor ID is required");
      }
      return getAppointmentDoctorDetails(doctorId, serviceId, date);
    },
    enabled: !!doctorId,
    staleTime: 0,
    retry: 1,
  });
};

export const useConsultationTypes = (
  doctorId: string | null,
  serviceId: string,
) => {
  return useQuery<ConsultationTypesResponse, Error>({
    queryKey: ["consultationTypes", doctorId, serviceId],
    queryFn: () => {
      if (!doctorId) {
        throw new Error("Doctor ID is required");
      }
      return getConsultationTypes(doctorId, serviceId);
    },
    enabled: !!doctorId,
    staleTime: 0,
    retry: 1,
  });
};

export const useTimeSlots = (
  doctorId: string | null,
  serviceId: string | null,
  preferredDate: string,
  consultationMode: "IN_CLINIC" | "TELECONSULTATION" | null,
) => {
  return useQuery<TimeSlotsResponse, Error>({
    queryKey: [
      "timeSlots",
      doctorId,
      serviceId,
      preferredDate,
      consultationMode,
    ],
    queryFn: async () => {
      if (!doctorId || !serviceId || !preferredDate || !consultationMode) {
        throw new Error("Missing required parameters for time slots");
      }
      return getTimeSlots(doctorId, serviceId, preferredDate, consultationMode);
    },
    enabled: !!doctorId && !!serviceId && !!preferredDate && !!consultationMode,
    staleTime: 0,
    retry: 1,
  });
};

export const useDoctorTimeOff = (doctorId: string | null) => {
  return useQuery<TimeOffData, Error>({
    queryKey: ["doctorTimeOff", doctorId],
    queryFn: async () => {
      if (!doctorId) {
        throw new Error("Doctor ID is required");
      }
      return getDoctorTimeOff(doctorId);
    },
    enabled: !!doctorId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1,
  });
};
