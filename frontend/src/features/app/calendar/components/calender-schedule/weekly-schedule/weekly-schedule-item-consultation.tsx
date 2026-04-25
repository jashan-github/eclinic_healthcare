import type { DoctorSchedule } from "@/types/calendar";
import { format, parse } from "date-fns";
import type { FC, ReactElement } from "react";

interface WeeklyScheduleItemConsultationProps {
  schedule: DoctorSchedule;
}

const WeeklyScheduleItemConsultation: FC<
  WeeklyScheduleItemConsultationProps
> = ({ schedule }): ReactElement => {
  const { appointment_services, start_time, end_time } = schedule;
  console.log(appointment_services);

  // Format time from HH:mm or HH:mm:ss to h:mm a
  const formatTime = (time: string | null) => {
    if (!time) return "—";
    try {
      // Handle both HH:mm and HH:mm:ss formats
      const timeStr = time.length > 5 ? time.substring(0, 5) : time;
      return format(parse(timeStr, "HH:mm", new Date()), "h:mm a");
    } catch {
      return time;
    }
  };

  const start = formatTime(start_time);
  const end = formatTime(end_time);

  // Determine consultation mode - check if we have service data with consultation_mode
  // For now, default to "In-clinic" - this could be enhanced if schedule includes consultation_mode
  // const consultationMode = 'In-clinic'

  // Format service names - join with comma
  const serviceNames = appointment_services?.length
    ? appointment_services.map((service) => service.service_name).join(", ")
    : null;

  return (
    <div
      className="w-fit rounded-lg border border-l-4 p-3 font-poppins"
      style={{
        borderImageSource:
          "radial-gradient(59.21% 50% at 0% 50%, #30AC41 100%, #E3F8E6 100%)",
        borderImageSlice: 1,
      }}
    >
      <div className="font-bold text-sm leading-5 text-gray-900">
        {start} - {end}
      </div>

      <div className="mt-1">
        {/* <div className="text-xs leading-4 text-gray-900">
          {consultationMode}
        </div> */}
        {serviceNames ? (
          <div className="text-xs leading-4 text-gray-900 mt-1">
            {serviceNames}
          </div>
        ) : (
          <div className="text-xs leading-4 text-gray-900 mt-1">
            No Services Listed
          </div>
        )}
      </div>
    </div>
  );
};

export default WeeklyScheduleItemConsultation;
