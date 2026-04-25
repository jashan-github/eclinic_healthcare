// src/hooks/use-calendar-schedule.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import type { ScheduleDay } from "@/types/calendar";
import {
  deleteScheduleSlot,
  getSchedule,
} from "../services/calendar-schedule-service";
import { toast } from "react-toastify";
import { useAuth } from "@/context/auth/auth-context-utils";

// GET: Weekly Schedule
export const useCalendarSchedule = () => {
  const { user } = useAuth();
  const doctorId = user?.id;

  const { data, isLoading, error } = useQuery<ScheduleDay[], Error>({
    queryKey: ["weeklySchedule", doctorId],
    queryFn: () => {
      if (!doctorId) {
        return Promise.resolve([]);
      }
      return getSchedule(doctorId);
    },
    enabled: !!doctorId,
    staleTime: 1000 * 60 * 5,
    refetchOnWindowFocus: false,
  });

  return {
    weeklySchedule: data ?? [], // nullish coalescing → safe empty array
    isLoading,
    error,
  };
};

// DELETE: Schedule Slot
export const useDeleteSchedule = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (scheduleId: string) => deleteScheduleSlot(scheduleId),
    onSuccess: () => {
      // Invalidate relevant queries so UI auto-refreshes
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
      toast.success("Slot deleted successfully");
    },
    onError: (error: any) => {
      toast.error(error?.message || "Failed to delete slot");
    },
  });

  return {
    deleteScheduleSlot: mutation.mutate,
    deleteSlotAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
  };
};
