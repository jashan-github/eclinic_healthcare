import { Divider, Stack } from "@mantine/core";
import { useCalendarSchedule } from "../../../hooks/use-calendar-schedule";
import WeeklyScheduleItem from "./weekly-schedule-item";

// type WeeklyScheduleProps = {
//   onChange: (hasChanges: boolean) => void
// }

// const WeeklySchedule = ({ onChange }: WeeklyScheduleProps) => {
const WeeklySchedule = () => {
  const { weeklySchedule } = useCalendarSchedule();

  // Define all days of the week - always show all 7 days regardless of API data
  const allDays = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];

  // Create a map of existing schedules by day name
  // Use empty array as fallback if weeklySchedule is undefined or null
  const scheduleMap = new Map(
    (weeklySchedule || []).map((schedule) => [
      schedule.day_name,
      schedule.doctor_schedules,
    ]),
  );

  // Merge API data with all days to ensure all days are shown
  // Always show all 7 days, even if API has no data or is still loading
  const allDaysWithSchedules = allDays.map((dayName) => ({
    day_name: dayName,
    doctor_schedules: scheduleMap.get(dayName) || [],
  }));
  console.log(allDaysWithSchedules);

  return (
    <div className="flex flex-col gap-lg">
      <h2 className="font-poppins text-base font-semibold text-[#0F1011] leading-6">
        Set your weekly schedule
      </h2>

      <div className="flex flex-col gap-4 overflow-y-auto pb-20 max-h-[500px] min-h-[400px]">
        {allDaysWithSchedules.map((wSchedule) => (
          <Stack key={wSchedule.day_name}>
            <WeeklyScheduleItem
              dayName={wSchedule.day_name}
              doctorSchedules={wSchedule.doctor_schedules}
            />
            <Divider />
          </Stack>
        ))}
      </div>
    </div>
  );
};

export default WeeklySchedule;
