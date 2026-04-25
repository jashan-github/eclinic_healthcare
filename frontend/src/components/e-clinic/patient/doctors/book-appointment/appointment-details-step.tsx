// appointment-details-step.tsx
import {
  CalendarIcon,
  MapPinIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react";
import RadioButton from "@/components/ui/radio-button";
import FormInput from "@/components/ui/form-input";
import {
  useTimeSlots,
  useDoctorTimeOff,
} from "@/hooks/use-appointment-doctor-details";
import { useEffect, useMemo } from "react";
import { toast } from "react-toastify";
import { DatePickerInput } from "@mantine/dates";

interface AppointmentDetailsStepProps {
  consultationType: "teleconsultation" | "in-clinic" | null;
  selectedDate: string;
  selectedTime?: string;
  doctorId?: string;
  serviceId?: string;
  symptoms?: string;
  onConsultationTypeChange: (type: "teleconsultation" | "in-clinic") => void;
  onDateChange: (date: string) => void;
  onTimeChange: (time: string) => void;
  onSymptomsChange: (symptoms: string) => void;
  onNext: (payload: any) => void;
  showInclinic: boolean;
  showTele: boolean;
}

const AppointmentDetailsStep = ({
  consultationType,
  selectedDate,
  selectedTime,
  doctorId,
  serviceId,
  symptoms,
  onConsultationTypeChange,
  onDateChange,
  onTimeChange,
  onSymptomsChange,
  onNext,
  showInclinic,
  showTele,
}: AppointmentDetailsStepProps) => {
  const consultationMode =
    consultationType === "in-clinic"
      ? "IN_CLINIC"
      : consultationType === "teleconsultation"
        ? "TELECONSULTATION"
        : null;

  // Fetch time-off periods and booking window for the doctor
  const { data: timeOffData } = useDoctorTimeOff(doctorId || null);
  const timeOffPeriods = timeOffData?.periods || [];
  const bookingWindowDays = timeOffData?.booking_window_days || 30;

  // Calculate max date based on booking window
  const maxDate = useMemo(() => {
    const today = new Date();
    const max = new Date(today);
    max.setDate(today.getDate() + bookingWindowDays);
    return max;
  }, [bookingWindowDays]);

  const {
    data: timeSlotsData,
    isLoading: loadingSlots,
    isError: slotsError,
  } = useTimeSlots(
    doctorId || null,
    serviceId || null,
    selectedDate,
    selectedDate && consultationType ? consultationMode : null,
  );

  // Helper function to check if a date is blocked (has any time-off period)
  const isDateBlocked = useMemo(() => {
    return (date: Date | string): boolean => {
      if (!date || timeOffPeriods.length === 0) return false;

      const checkDate = date instanceof Date ? date : new Date(date);
      checkDate.setHours(0, 0, 0, 0);

      return timeOffPeriods.some((period) => {
        const startDate = new Date(period.start_datetime);
        const endDate = new Date(period.end_datetime);
        startDate.setHours(0, 0, 0, 0);
        endDate.setHours(0, 0, 0, 0);

        // Check if the date falls within any blocked period
        return checkDate >= startDate && checkDate <= endDate;
      });
    };
  }, [timeOffPeriods]);

  // Helper function to check if a time slot is blocked
  const isTimeSlotBlocked = useMemo(() => {
    return (
      dateStr: string,
      timeStr: string,
      slotDurationMinutes: number = 30,
    ): boolean => {
      if (!dateStr || !timeStr || timeOffPeriods.length === 0) return false;

      // Convert display time (e.g., "09:00 AM") to 24-hour format
      const [time, ampm] = timeStr.split(" ");
      const [hour, minute] = time.split(":");
      let h = parseInt(hour);
      if (ampm === "PM" && h !== 12) h += 12;
      if (ampm === "AM" && h === 12) h = 0;
      const time24 = `${h.toString().padStart(2, "0")}:${minute}:00`;

      // Create datetime for slot start and end (assuming 30 min duration by default)
      const slotStart = new Date(`${dateStr}T${time24}`);
      const slotEnd = new Date(
        slotStart.getTime() + slotDurationMinutes * 60 * 1000,
      );

      return timeOffPeriods.some((period) => {
        const periodStart = new Date(period.start_datetime);
        const periodEnd = new Date(period.end_datetime);

        // Check if the slot overlaps with the blocked period
        // Slot overlaps if: slotStart < periodEnd && slotEnd > periodStart
        return slotStart < periodEnd && slotEnd > periodStart;
      });
    };
  }, [timeOffPeriods]);

  const formatBackendTime = (time: string) => {
    const [hour, minute] = time.split(":");
    let h = parseInt(hour);
    const ampm = h >= 12 ? "PM" : "AM";
    h = h % 12 || 12;
    return `${h.toString().padStart(2, "0")}:${minute} ${ampm}`;
  };

  const availableTimeSlots = useMemo(() => {
    if (!timeSlotsData?.time_slots) return [];

    const now = new Date();
    const todayStr = now.toISOString().split("T")[0];

    return timeSlotsData.time_slots
      .map((slot) => {
        const displayTime = formatBackendTime(slot.time);
        const slotDuration = slot.duration_minutes || 30;
        const isBlockedByTimeOff = isTimeSlotBlocked(
          selectedDate,
          displayTime,
          slotDuration,
        );

        let isPast = false;
        if (selectedDate === todayStr) {
          const [h, m] = slot.time.split(":").map(Number);
          const slotDateTime = new Date(now);
          slotDateTime.setHours(h, m, 0, 0);

          isPast = slotDateTime <= now;
        }

        const isAvailable = slot.is_available && !isBlockedByTimeOff && !isPast;

        return {
          display: displayTime,
          isAvailable,
          isPast,
          isBlockedByTimeOff,
          sortKey: (() => {
            const [hour, minute] = slot.time.split(":");
            return parseInt(hour) * 60 + parseInt(minute);
          })(),
        };
      })
      .sort((a, b) => a.sortKey - b.sortKey);
  }, [timeSlotsData, selectedDate, isTimeSlotBlocked]);

  // Reset selected date if it becomes blocked
  useEffect(() => {
    if (selectedDate) {
      const dateObj = new Date(selectedDate);
      if (isDateBlocked(dateObj)) {
        onDateChange("");
        onTimeChange("");
        toast.error(
          "The selected date is not available. Please choose another date.",
        );
      }
    }
  }, [selectedDate, isDateBlocked, onDateChange, onTimeChange]);

  // Reset selected time if it's no longer available or blocked
  useEffect(() => {
    if (!loadingSlots && !slotsError && selectedTime && selectedDate) {
      const isStillAvailable = availableTimeSlots.some(
        (slot) => slot.display === selectedTime && slot.isAvailable,
      );
      if (!isStillAvailable) {
        onTimeChange(""); // Reset if not available anymore
      }
    }
  }, [
    availableTimeSlots,
    loadingSlots,
    slotsError,
    selectedTime,
    selectedDate,
    onTimeChange,
  ]);
  // Convert display time → backend format for payload
  const convertToBackendTime = (displayTime: string) => {
    const [time, ampm] = displayTime.split(" ");
    const [hour, minute] = time.split(":");
    let h = parseInt(hour);
    if (ampm === "PM" && h !== 12) h += 12;
    if (ampm === "AM" && h === 12) h = 0;
    return `${h.toString().padStart(2, "0")}:${minute}:00`;
  };

  const handleNextClick = () => {
    if (!consultationType) {
      toast.error("Please select a consultation type");
      return;
    }

    if (!selectedTime) {
      toast.error("Please select a time slot");
      return;
    }

    // Double-check that date and time are not blocked
    if (selectedDate) {
      const dateObj = new Date(selectedDate);
      if (isDateBlocked(dateObj)) {
        toast.error(
          "The selected date is not available. Please choose another date.",
        );
        return;
      }
    }

    // Find the slot duration from the available slots
    const selectedSlot = timeSlotsData?.time_slots?.find((slot) => {
      const displayTime = formatBackendTime(slot.time);
      return displayTime === selectedTime;
    });
    const slotDuration = selectedSlot?.duration_minutes || 30;

    if (
      selectedDate &&
      selectedTime &&
      isTimeSlotBlocked(selectedDate, selectedTime, slotDuration)
    ) {
      toast.error(
        "The selected time slot is not available. Please choose another time.",
      );
      return;
    }

    const backendTime = convertToBackendTime(selectedTime);

    const payload = {
      doctor_id: doctorId || "",
      service_id: serviceId || "",
      consultation_mode: consultationMode,
      preferred_date: selectedDate,
      preferred_time: backendTime,
      reason: symptoms?.trim() || "No reason provided",
    };

    onNext(payload);
  };

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6">
      <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-6">
        Appointment Details
      </h2>

      <div className="space-y-6">
        {/* Consultation Type */}
        <div>
          <label className="block mb-3 font-poppins font-medium text-sm text-[#545D69]">
            Select Consultation Type
          </label>

          <div className="flex flex-row lg:flex-col gap-3">
            {showTele && (
              <div className="w-1/2 lg:w-full">
                <RadioButton
                  value="teleconsultation"
                  checked={consultationType === "teleconsultation"}
                  onChange={(value) => {
                    onConsultationTypeChange(value as "teleconsultation");
                    onTimeChange(""); // Reset time slot when consultation type changes
                  }}
                  name="consultationType"
                  icon={
                    <VideoCameraIcon
                      size={20}
                      weight="bold"
                      className="text-[#002FD4]"
                    />
                  }
                  title="Teleconsultation"
                  description="Video call from your home"
                />
              </div>
            )}

            {showInclinic && (
              <div className="w-1/2 lg:w-full">
                <RadioButton
                  value="in-clinic"
                  checked={consultationType === "in-clinic"}
                  onChange={(value) => {
                    onConsultationTypeChange(value as "in-clinic");
                    onTimeChange(""); // Reset time slot when consultation type changes
                  }}
                  name="consultationType"
                  icon={
                    <MapPinIcon
                      size={20}
                      weight="bold"
                      className="text-[#002FD4]"
                    />
                  }
                  title="In-Clinic"
                  description="Visit the clinic"
                />
              </div>
            )}
          </div>
        </div>

        {/* Preferred Date */}
        <div className="w-[50%] lg:w-full">
          <label className="block mb-2 font-poppins font-medium text-[14px] text-[#545D69]">
            Preferred Date
          </label>
          <DatePickerInput
            value={selectedDate ? new Date(selectedDate) : null}
            onChange={(value: string | null) => {
              if (!value) {
                onDateChange("");
                return;
              }
              // Convert string to Date
              const date = new Date(value);
              if (isNaN(date.getTime())) {
                onDateChange("");
                return;
              }
              // Check if date is blocked
              if (isDateBlocked(date)) {
                toast.error(
                  "This date is not available. Please select another date.",
                );
                return;
              }
              // Check if date is beyond booking window
              if (date > maxDate) {
                toast.error(
                  `Bookings are only allowed up to ${bookingWindowDays} days in advance.`,
                );
                return;
              }
              // Convert Date to YYYY-MM-DD format
              const year = date.getFullYear();
              const month = String(date.getMonth() + 1).padStart(2, "0");
              const day = String(date.getDate()).padStart(2, "0");
              onDateChange(`${year}-${month}-${day}`);
            }}
            minDate={new Date()}
            maxDate={maxDate}
            placeholder="Select date"
            getDayProps={(date) => {
              const dateObj = new Date(date);
              // Disable blocked dates in the calendar
              if (isDateBlocked(dateObj)) {
                return {
                  disabled: true,
                  style: {
                    opacity: 0.5,
                    cursor: "not-allowed",
                  },
                };
              }
              // Disable dates beyond booking window
              if (dateObj.getTime() > maxDate.getTime()) {
                return {
                  disabled: true,
                  style: {
                    opacity: 0.3,
                    cursor: "not-allowed",
                    textDecoration: "line-through",
                  },
                };
              }
              return {};
            }}
            rightSection={<CalendarIcon size={20} weight="bold" />}
            styles={{
              input: {
                border: "1px solid #E4E1FA",
                borderRadius: "8px",
                fontFamily: "Poppins, sans-serif",
                fontSize: "14px",
                height: "40px",
              },
            }}
          />
        </div>

        {/* Preferred Time - Only backend slots */}
        <div>
          <label className="block mb-3 font-poppins font-medium text-[14px] text-[#545D69]">
            Preferred Time
          </label>

          {!consultationType ? (
            <p className="text-sm text-[#64748B] font-medium text-center py-8">
              Please select a consultation type to view available slots.
            </p>
          ) : loadingSlots ? (
            <p className="text-sm text-[#64748B]">
              Loading available time slots...
            </p>
          ) : slotsError ? (
            <p className="text-sm text-red-500">
              Failed to load time slots. Please try again later.
            </p>
          ) : availableTimeSlots.length === 0 ? (
            <p className="text-sm text-orange-600 font-medium text-center py-8">
              Slots not available for the selected date and consultation type.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              {availableTimeSlots.map(({ display: time, isAvailable }) => (
                <button
                  key={time}
                  type="button"
                  onClick={() => isAvailable && onTimeChange(time)}
                  disabled={!isAvailable}
                  className={`px-4 py-2.5 rounded-md border-2 font-poppins font-medium text-[14px] leading-[20px] transition-all ${
                    selectedTime === time && isAvailable
                      ? "border-[#002FD4] bg-[#002FD4] text-white"
                      : isAvailable
                        ? "border-[#E4E5ED] bg-white text-[#0F1011] hover:bg-[#F4F6F9]"
                        : "border-gray-300 bg-gray-100 text-gray-500 cursor-not-allowed"
                  }`}
                >
                  {time}
                  {!isAvailable && (
                    <span className="block text-xs mt-1">Not Available</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Symptoms */}
        <FormInput
          as="textarea"
          label="Describe your symptoms or reason for visit"
          value={symptoms}
          onChange={(e) => onSymptomsChange(e.target.value)}
          placeholder="Please describe your symptoms, concerns, or reason for the consultation..."
          rows={5}
        />

        {/* Next Button */}
        <div className="flex justify-start lg:justify-end">
          <button
            type="button"
            onClick={handleNextClick}
            disabled={
              !consultationType ||
              !selectedTime ||
              loadingSlots ||
              !symptoms?.trim()
            }
            className="bg-[#002FD4] hover:bg-[#001FB8] disabled:opacity-60 disabled:cursor-not-allowed text-white font-poppins font-semibold text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default AppointmentDetailsStep;
