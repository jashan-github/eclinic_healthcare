// appointment-management.tsx

import { useState, useMemo } from "react";
import AppointmentManagementTabs from "./appointment-management-tabs";
import SingleEntry from "./single-entry";
import { MagnifyingGlassIcon } from "@phosphor-icons/react";
import { Select, TextInput, Loader } from "@mantine/core";
import { useStaffAssignedDoctorAppointments } from "@/hooks/use-staff";
import { format } from "date-fns";
import { useDebouncedValue } from "@mantine/hooks";

type Appointment = {
  appointment_date: string;
  name: string;
  email: string;
  type: "Teleconsultation" | "In-Clinic";
  time: string;
  doctor: string;
  duration: number;
  status: "Confirmed" | "Pending";
  paymentStatus: "Paid" | "Unpaid";
  paymentMethod?: string;
  contactNumber: string;
  emergencyContact: string;
  familyContact: string;
  patientId: string;
  serviceName: string;
  amount: string;
};

export default function AppointmentManagement() {
  const [activeTab, setActiveTab] = useState<"Today" | "Upcoming">("Today");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch] = useDebouncedValue(searchQuery, 500);
  const [typeFilter, setTypeFilter] = useState<
    "All" | "Teleconsultation" | "In-Clinic"
  >("All");

  // Fetch appointments based on active tab and search
  const { data: todayData, isLoading: isLoadingToday } =
    useStaffAssignedDoctorAppointments({
      type: "today",
      search: debouncedSearch || undefined,
      page: 1,
      per_page: 100,
    });

  const { data: upcomingData, isLoading: isLoadingUpcoming } =
    useStaffAssignedDoctorAppointments({
      type: "upcoming",
      search: debouncedSearch || undefined,
      page: 1,
      per_page: 100,
    });

  // Transform API data to Appointment format

  const doctorName = useMemo(() => {
    const source =
      activeTab === "Today"
        ? todayData?.data?.doctor_profile
        : upcomingData?.data?.doctor_profile;

    if (!source) return "Unknown";

    return `${source.first_name ?? ""} ${source.last_name ?? ""}`.trim();
  }, [activeTab, todayData, upcomingData]);

  const transformAppointment = (item: any, doctorName: string): Appointment => {
    console.log(item);

    const formatTime = (timeString: string) => {
      try {
        const [hours, minutes] = timeString.split(":").map(Number);
        const date = new Date();
        date.setHours(hours, minutes);
        return format(date, "hh:mm a");
      } catch {
        return timeString;
      }
    };

    const getPaymentStatus = (status?: string): "Paid" | "Unpaid" => {
      if (!status) return "Unpaid";
      const upperStatus = status.toUpperCase();
      return upperStatus === "PAID" || upperStatus === "COMPLETED"
        ? "Paid"
        : "Unpaid";
    };

    const getStatus = (status: string): "Confirmed" | "Pending" => {
      const upperStatus = status.toUpperCase();
      return upperStatus === "CONFIRMED" || upperStatus === "ACCEPTED"
        ? "Confirmed"
        : "Pending";
    };

    return {
      appointment_date: item.appointment_date || "",
      name: item.patient_name || "Unknown",
      email: item.patient_email || "",
      type:
        item.consultation_mode === "TELECONSULTATION"
          ? "Teleconsultation"
          : "In-Clinic",
      time: formatTime(item.start_time || ""),
      doctor: doctorName,
      duration: item.duration_minutes || 30,
      status: getStatus(item.status || "PENDING"),
      paymentStatus: getPaymentStatus(item.payment_status),
      paymentMethod: item.payment_method || item.payment_type || undefined,
      contactNumber: item.patient_phone || "N/A",
      emergencyContact: item.emergency_contact || "N/A",
      familyContact: item.family_contact || "N/A",
      patientId: item.patient_id || "",
      serviceName: item.service_name || "Consultation",
      amount: `${item.price_amount ?? 0} ${item.currency ?? ""}`,
    };
  };

  const todayAppointments: Appointment[] = useMemo(() => {
    return (todayData?.data?.appointments || []).map((item: any) =>
      transformAppointment(item, doctorName),
    );
  }, [todayData, doctorName]);

  const upcomingAppointments: Appointment[] = useMemo(() => {
    return (upcomingData?.data?.appointments || []).map((item: any) =>
      transformAppointment(item, doctorName),
    );
  }, [upcomingData, doctorName]);

  const currentAppointments =
    activeTab === "Today" ? todayAppointments : upcomingAppointments;
  const isLoading = activeTab === "Today" ? isLoadingToday : isLoadingUpcoming;

  // Filter by consultation type (client-side filter since API doesn't support it)
  const filteredAppointments = useMemo(() => {
    if (typeFilter === "All") {
      return currentAppointments;
    }
    return currentAppointments.filter((appt) => {
      return appt.type === typeFilter;
    });
  }, [currentAppointments, typeFilter]);

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="mb-6 flex-shrink-0">
        <AppointmentManagementTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          todayLength={
            todayData?.data?.pagination?.total || todayAppointments.length
          }
          UpcomingLength={
            upcomingData?.data?.pagination?.total || upcomingAppointments.length
          }
        />
      </div>

      {/* Search + Type Filter */}
      <div className="flex gap-4 mb-6 flex-shrink-0">
        <TextInput
          placeholder="Search by patient name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.currentTarget.value)}
          leftSection={<MagnifyingGlassIcon size={18} weight="bold" />}
          className="flex-1"
          radius="md"
          size="md"
        />

        <Select
          placeholder="Filter by type"
          value={typeFilter}
          onChange={(value) =>
            setTypeFilter(value as "All" | "Teleconsultation" | "In-Clinic")
          }
          data={[
            { value: "All", label: "All Entries" },
            { value: "Teleconsultation", label: "Teleconsultation" },
            { value: "In-Clinic", label: "In-Clinic" },
          ]}
          radius="md"
          size="md"
          className="w-64"
        />
      </div>

      {/* Scrollable List */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader size="md" />
          </div>
        ) : filteredAppointments.length > 0 ? (
          filteredAppointments.map((appt, index) => (
            <SingleEntry
              key={`${activeTab}-${appt.name}-${index}`}
              date={appt?.appointment_date}
              name={appt.name}
              email={appt.email}
              type={appt.type}
              time={appt.time}
              doctor={appt.doctor}
              duration={appt.duration}
              status={appt.status}
              paymentStatus={appt.paymentStatus}
              paymentMethod={appt.paymentMethod}
              contactNumber={appt.contactNumber}
              emergencyContact={appt.emergencyContact}
              familyContact={appt.familyContact}
              patientId={appt.patientId}
              serviceName={appt.serviceName} // ADD
              amount={appt.amount}
            />
          ))
        ) : (
          <div className="text-center py-20 text-gray-500 font-medium">
            {debouncedSearch || typeFilter !== "All"
              ? "No appointments match your search or filter"
              : `No ${activeTab.toLowerCase()} appointments`}
          </div>
        )}
      </div>
    </div>
  );
}
