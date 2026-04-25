// src/components/e-clinic/doctor/appointments/my-opd.tsx
import TodayAppointment from "@/components/e-clinic/doctor/appointments/today-appointments";
import type {
  AppointmentItem,
  PaginatedAppointments,
} from "@/services/appointment-service";
import { type FC, type ReactElement, useMemo } from "react";
import { Button } from "@mantine/core";
import { CaretLeftIcon, CaretRightIcon } from "@phosphor-icons/react";

interface MyOPDProps {
  appointments: AppointmentItem[];
  searchTerm?: string;
  sortAsc?: boolean | null;
  consultationFilter?: "online" | "offline" | null;
  pagination?: PaginatedAppointments;
  currentPage?: number;
  onPageChange?: (page: number) => void;
}

const MyOPD: FC<MyOPDProps> = ({
  appointments = [],
  searchTerm = "",
  sortAsc = null,
  consultationFilter = null,
  pagination,
  currentPage = 1,
  onPageChange,
}): ReactElement => {
  const filteredAndSorted = useMemo(() => {
    let filtered = appointments;

    // Search by patient name
    if (searchTerm.trim()) {
      filtered = filtered.filter((apt) =>
        apt.patient_name.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    // Consultation filter
    if (consultationFilter === "online") {
      filtered = filtered.filter(
        (apt) => apt.consultation_mode === "TELECONSULTATION",
      );
    } else if (consultationFilter === "offline") {
      filtered = filtered.filter(
        (apt) => apt.consultation_mode === "IN_CLINIC",
      );
    }

    // Sort by time
    if (sortAsc !== null) {
      filtered = [...filtered].sort((a, b) => {
        const cmp = a.start_time.localeCompare(b.start_time);
        return sortAsc ? cmp : -cmp;
      });
    }

    return filtered;
  }, [appointments, searchTerm, sortAsc, consultationFilter]);

  if (filteredAndSorted.length === 0) {
    return (
      <div className="bg-white w-full p-6 rounded-xl">
        <div className="text-center py-12 text-gray-500 font-poppins">
          No appointments found
        </div>
      </div>
    );
  }

  const showPagination = pagination && pagination.last_page > 1;

  return (
    <div className="bg-white w-full rounded-xl">
      <div className="space-y-6 p-6">
        {filteredAndSorted.map((item) => (
          <TodayAppointment
            key={item.id}
            id={item.id}
            name={item.patient_name}
            gender={item.patient_gender === "male" ? "M" : "F"}
            age={item.patient_age}
            image={item.patient_profile_image || ""}
            isInClinic={item.consultation_mode === "IN_CLINIC"}
            timeSpan={item.duration_minutes}
            timeSlot={item.start_time}
            timeEnd={item.end_time}
            amount={item.price_amount}
            currency={item.currency}
            paymentMode={item.payment_type}
            isAppointmentRequest={item.is_appointment_request || false}
            sessionId={item.session_id}
            canStartCall={true}
            amount_before_waiver={item?.amount_before_waiver}
            waiver_percent={item?.waiver_percent}
            serviceName={item?.service_name}
          />
        ))}
      </div>

      {showPagination && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
          <div className="text-sm text-gray-600 font-poppins">
            Showing {pagination.from} to {pagination.to} of {pagination.total}{" "}
            appointments
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(currentPage - 1)}
              disabled={currentPage === 1}
              leftSection={<CaretLeftIcon size={16} />}
            >
              Previous
            </Button>
            <div className="text-sm text-gray-700 font-poppins px-3">
              Page {currentPage} of {pagination.last_page}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(currentPage + 1)}
              disabled={currentPage >= pagination.last_page}
              rightSection={<CaretRightIcon size={16} />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyOPD;
