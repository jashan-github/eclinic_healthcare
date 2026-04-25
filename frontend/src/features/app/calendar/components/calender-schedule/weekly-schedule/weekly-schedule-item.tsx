import type { DoctorSchedule } from "@/types/calendar";
import { CheckIcon, PencilIcon } from "@phosphor-icons/react";
import { memo, useMemo, useState, useEffect, useRef } from "react";
import { toast } from "react-toastify";
import { v4 as uuidv4 } from "uuid";
import WeeklyScheduleItemConsultation from "./weekly-schedule-item-consultation";
import WeeklyScheduleItemSlot, {
  type WeeklyScheduleItemSlotHandle,
} from "./weekly-schedule-item-slot";
import { useDeleteSchedule } from "../../../hooks/use-calendar-schedule";
import { useCreateDoctorAvailability } from "@/hooks/use-weekly-schedule";
import { buildCreateAvailabilityPayload } from "@/services/weekly-schedule";
import { useAuth } from "@/context/auth/auth-context-utils";

// interface Props {
//   dayName: string
//   doctorSchedules: DoctorSchedule[]
//   onChange: (hasChanges: boolean) => void
// }

interface Props {
  dayName: string;
  doctorSchedules: DoctorSchedule[];
}

// const WeeklyScheduleItem = memo(({ dayName, doctorSchedules, onChange }: Props) => {
const WeeklyScheduleItem = memo(({ dayName, doctorSchedules }: Props) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);

  const [localDoctorSchedules, setLocalDoctorSchedules] =
    useState(doctorSchedules);
  console.log(localDoctorSchedules);

  const { deleteScheduleSlot } = useDeleteSchedule();
  const createAvailabilityMutation = useCreateDoctorAvailability();
  const { user } = useAuth();
  // console.log('doctorSchedules', user)
  const slotRefs = useRef<Map<string, WeeklyScheduleItemSlotHandle>>(new Map());

  // Update local state when doctorSchedules prop changes (e.g., after deletion)
  useEffect(() => {
    if (!isEditing) {
      setLocalDoctorSchedules(doctorSchedules);
    }
  }, [doctorSchedules, isEditing]);
  const addNewSlot = async (): Promise<void> => {
    let startTime = "09:00";
    let endTime = "10:00";

    if (localDoctorSchedules.length > 0) {
      const sorted = [...localDoctorSchedules].sort((a, b) =>
        a.start_time!.localeCompare(b.start_time!),
      );
      const lastSlot = sorted[sorted.length - 1];

      if (lastSlot?.end_time) {
        const [h, m] = lastSlot.end_time.split(":").map(Number);
        const next = new Date();
        next.setHours(h, m);
        next.setMinutes(next.getMinutes() + 60);

        startTime = next.toTimeString().slice(0, 5);
        const end = new Date(next.getTime() + 60 * 60 * 1000);
        endTime = end.toTimeString().slice(0, 5);
      }
    }

    // Create availability via API immediately so service selection is available
    if (user?.id) {
      const payload = buildCreateAvailabilityPayload(
        dayName,
        startTime,
        endTime,
        user.clinic_id,
      );

      try {
        const response = await createAvailabilityMutation.mutateAsync({
          doctorId: user.id,
          payload,
        });
        const createdId = response?.data?.id;
        if (createdId) {
          setLocalDoctorSchedules((prev) => [
            ...prev,
            {
              id: createdId,
              draft: false,
              day_name: dayName,
              start_time: startTime,
              end_time: endTime,
              day_off: 0,
              clinic_id: user.clinic_id,
              appointment_services: [],
            } as DoctorSchedule,
          ]);
        } else {
          // Fallback: add as draft if no ID returned
          const slotId = uuidv4();
          setLocalDoctorSchedules((prev) => [
            ...prev,
            {
              id: slotId,
              draft: true,
              day_name: dayName,
              start_time: startTime,
              end_time: endTime,
              day_off: 0,
              clinic_id: user.clinic_id,
              appointment_services: [],
            } as DoctorSchedule,
          ]);
        }
      } catch {
        toast.error("Failed to create availability slot");
      }
    }
  };

  const deleteSlot = (slotId: string): void => {
    // Optimistically update local state
    const updatedSchedules = localDoctorSchedules.filter(
      (s) => s.id !== slotId,
    );
    setLocalDoctorSchedules(updatedSchedules);

    // Call API to delete
    deleteScheduleSlot(slotId);

    // If no schedules left, exit edit mode
    if (updatedSchedules.length === 0) {
      setIsEditing(false);
    }
  };

  const hasSchedules = useMemo(
    () => doctorSchedules.length > 0,
    [doctorSchedules],
  );

  const onToggleEdit = async () => {
    if (isEditing) {
      // Save all draft slots before exiting edit mode
      const draftSlots = localDoctorSchedules.filter((s) => s.draft || !s.id);
      console.log(draftSlots);

      if (draftSlots.length > 0) {
        // Save all draft slots
        const savePromises = draftSlots.map(async (slot) => {
          const slotRef = slotRefs.current.get(slot.id);
          if (slotRef?.saveAvailability) {
            try {
              await slotRef.saveAvailability();
            } catch (error) {
              console.error("Failed to save slot:", error);
            }
          } else if (slot.start_time && slot.end_time && user?.id) {
            // Fallback: create availability directly
            const payload = buildCreateAvailabilityPayload(
              slot.day_name,
              slot.start_time,
              slot.end_time,
              user.clinic_id,
            );

            try {
              await createAvailabilityMutation.mutateAsync({
                doctorId: user.id,
                payload,
              });
              toast.success("Availability saved!");
            } catch (error) {
              toast.error("Failed to save availability");
              throw error;
            }
          }
        });

        try {
          await Promise.all(savePromises);
          // Refresh schedules after saving
          setLocalDoctorSchedules(doctorSchedules);
          setIsEditing(false);
        } catch (error) {
          toast.error("Some slots failed to save. Please check and try again.");
          // Don't exit edit mode if save failed
        }
      } else {
        // No draft slots, just exit edit mode
        setLocalDoctorSchedules(doctorSchedules);
        setIsEditing(false);
      }
    } else {
      setLocalDoctorSchedules([...doctorSchedules]);
      if (doctorSchedules.length === 0 && user?.id) {
        // No existing slots - auto-create availability via API with default time
        const defaultStartTime = "09:00";
        const defaultEndTime = "10:00";
        const payload = buildCreateAvailabilityPayload(
          dayName,
          defaultStartTime,
          defaultEndTime,
          user.clinic_id,
        );

        try {
          const response = await createAvailabilityMutation.mutateAsync({
            doctorId: user.id,
            payload,
          });
          const createdId = response?.data?.id;
          if (createdId) {
            // Add slot with real ID (not draft) so service dropdown shows immediately
            setLocalDoctorSchedules([
              {
                id: createdId,
                draft: false,
                day_name: dayName,
                start_time: defaultStartTime,
                end_time: defaultEndTime,
                day_off: 0,
                clinic_id: user.clinic_id,
                appointment_services: [],
              } as DoctorSchedule,
            ]);
          } else {
            // Fallback: add as draft if no ID returned
            addNewSlot();
          }
        } catch {
          toast.error("Failed to create availability slot");
          return; // Don't enter edit mode if API failed
        }
      }
      setIsEditing(true);
    }
  };
  const handleScheduleUpdated = () => {
    // Schedule updated - refetch will happen via query invalidation
  };
  return (
    <div className="flex gap-6">
      <div className="w-1/6 flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={onToggleEdit}
            className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors ${
              isEditing
                ? "bg-[#002FD4] text-white"
                : "bg-[#F4F6F9] text-black hover:bg-gray-300"
            }`}
          >
            {isEditing ? <CheckIcon size={16} /> : <PencilIcon size={16} />}
          </button>

          <span className="font-poppins text-base font-medium text-[#0F1011]">
            {dayName.slice(0, 3).toUpperCase()}
          </span>
        </div>
      </div>

      <div className="flex-1">
        {isEditing ? (
          localDoctorSchedules.map((schedule) => (
            <WeeklyScheduleItemSlot
              key={schedule.id}
              ref={(el: any) => {
                if (el && el.saveAvailability) {
                  slotRefs.current.set(schedule.id, el);
                }
              }}
              initialData={schedule}
              showDeleteButton={localDoctorSchedules.length > 0}
              onAddNewSlot={addNewSlot}
              onDelete={deleteSlot}
              onScheduleUpdated={handleScheduleUpdated}
              onServiceAdded={() => {
                setLocalDoctorSchedules(doctorSchedules);
                setIsEditing(false);
              }}
            />
          ))
        ) : hasSchedules ? (
          doctorSchedules.map((schedule) => (
            <WeeklyScheduleItemConsultation
              key={schedule.id}
              schedule={schedule}
            />
          ))
        ) : (
          <span className="text-sm text-gray-500">Unavailable</span>
        )}
      </div>
    </div>
  );
});

export default WeeklyScheduleItem;
