import { useQuery } from "@tanstack/react-query";
import {
  fetchPatientWebinars,
  type PatientWebinarsResponse,
} from "@/services/patient-webinar-service";
import { format, parseISO } from "date-fns";
import type { UserRoleType } from "@/utils/user-role";

export interface AdminWebinarHost {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  role: UserRoleType;
  speciality?: string;
}
export interface TransformedWebinar {
  id: string;
  doctorName: string;
  doctorSpecialty: string;
  doctorImage: string;
  doctorExperience?: string;
  doctorDescription?: string;
  title: string;
  date: string; // Formatted: "Dec 25, 2024"
  time: string; // Formatted: "2:00 PM - 3:00 PM"
  duration: string; // Formatted: "60 mins"
  capacity: {
    filled: number;
    total: number;
  };
  host?: AdminWebinarHost;
  price: number | null;
  pricingType: "free" | "paid";
  can_join: boolean; // True if free and within 15 minutes before start
  startDateTime: Date; // Raw datetime for calculations
  webinarDescription?: string;
  currency?: string;
  host_id: string;
  is_registered: boolean;
}

export interface PatientWebinarsData {
  webinars: TransformedWebinar[];
  totalWebinars: number;
  freeWebinars: number;
  paidWebinars: number;
  registeredWebinars: number;
  isLoading: boolean;
  error: Error | null;
}

export const usePatientWebinars = (): PatientWebinarsData => {
  const { data, isLoading, error } = useQuery<PatientWebinarsResponse, Error>({
    queryKey: ["patientWebinars"],
    queryFn: fetchPatientWebinars,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });

  const webinars: TransformedWebinar[] = (data?.data?.webinars || []).map(
    (webinar) => {
      // Combine date and time for proper datetime formatting
      const startDateTime = `${webinar.webinar_date}T${webinar.start_time}`;
      const endDateTime = `${webinar.webinar_date}T${webinar.end_time}`;

      // Calculate duration in minutes
      const startDate = parseISO(startDateTime);
      const endDate = parseISO(endDateTime);
      const durationMinutes = Math.round(
        (endDate.getTime() - startDate.getTime()) / (1000 * 60),
      );

      // Format date and time
      const formattedDate = format(startDate, "MMM dd, yyyy");
      const formattedTime = `${format(startDate, "h:mm a")} - ${format(endDate, "h:mm a")}`;

      return {
        id: webinar.id,
        doctorName: webinar.host.name || "Unknown",
        doctorSpecialty: webinar.host.speciality || "Healthcare Provider",
        doctorImage:
          webinar.host.profile_image || "/assets/icons/doctor-icon.svg",
        doctorExperience: webinar.host_experience,
        doctorDescription:
          webinar.description ||
          `Dr. ${webinar.host.name} is the speaker for this webinar`,
        title: webinar.title,
        date: formattedDate,
        host: webinar?.host,
        time: formattedTime,
        duration: `${durationMinutes} mins`,
        capacity: {
          filled: webinar.registered_count,
          total: webinar.participant_limit,
        },
        price:
          webinar.pricing_type === "free" ? null : parseFloat(webinar.price),
        pricingType: webinar.pricing_type,
        can_join: webinar.can_join,
        startDateTime: startDate,
        webinarDescription: webinar.description || webinar.agenda,
        currency: webinar.currency,
        host_id: webinar.host_id,
        is_registered: webinar.is_registered,
      };
    },
  );

  const totalWebinars = webinars.length;
  const freeWebinars = webinars.filter((w) => w.price === null).length;
  const paidWebinars = webinars.filter((w) => w.price !== null).length;
  const registeredWebinars = webinars.filter((w) => w.is_registered).length;

  return {
    webinars,
    totalWebinars,
    freeWebinars,
    paidWebinars,
    registeredWebinars,
    isLoading,
    error,
  };
};
