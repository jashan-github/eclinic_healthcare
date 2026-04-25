// src/hooks/use-weekly-schedule.ts
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { toast } from "react-toastify";
import {
  updateWeeklySchedule,
  createDoctorAvailability,
  updateDoctorAvailability,
  addDoctorService,
  assignServiceToAvailability,
  getAvailabilityServices,
  updateAvailabilityService,
  deleteAvailabilityService,
  deleteDoctorService,
  getDoctorServices,
  getAvailabilityServicePricing,
  getDoctorServicePricing,
  createAvailabilityServicePricing,
  updateAvailabilityServicePricing,
  deleteAvailabilityServicePricing,
  createDoctorServicePricing,
  updateDoctorServicePricing,
  deleteDoctorServicePricing,
  type CreateDoctorAvailabilityPayload,
  type UpdateDoctorAvailabilityPayload,
  type AddDoctorServicePayload,
  type AssignServiceToAvailabilityPayload,
  type UpdateAvailabilityServicePayload,
  type AvailabilityService,
  type DoctorService,
  type AvailabilityServicePricingResponse,
  type DoctorServicePricingResponse,
  type CreateAvailabilityServicePricingPayload,
  type UpdateAvailabilityServicePricingPayload,
  type CreateDoctorServicePricingPayload,
  type UpdateDoctorServicePricingPayload,
} from "@/services/weekly-schedule";

export const useUpdateWeeklySchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateWeeklySchedule,
    onSuccess: (data) => {
      toast.success(data.message || "Schedule saved successfully!");
      // Keep weekly schedule in sync after any update
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to save schedule");
    },
  });
};

export const useCreateDoctorAvailability = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      doctorId,
      payload,
    }: {
      doctorId: string;
      payload: CreateDoctorAvailabilityPayload;
    }) => createDoctorAvailability(doctorId, payload),
    onSuccess: (data) => {
      toast.success(data.message || "Availability created successfully!");
      // Invalidate weekly schedule to refetch with new data
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create availability");
    },
  });
};

export const useUpdateDoctorAvailability = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      availabilityId,
      payload,
    }: {
      availabilityId: string;
      payload: UpdateDoctorAvailabilityPayload;
    }) => updateDoctorAvailability(availabilityId, payload),
    onSuccess: (data) => {
      toast.success(data.message || "Availability updated successfully!");
      // Invalidate weekly schedule to refetch with updated data
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update availability");
    },
  });
};

export const useAddDoctorService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AddDoctorServicePayload) => addDoctorService(payload),
    onSuccess: () => {
      // Invalidate doctor services to refetch
      queryClient.invalidateQueries({ queryKey: ["calendarServices"] });
    },
    onError: (error: Error) => {
      // Don't show toast here, let the calling component handle it
      throw error;
    },
  });
};

export const useAssignServiceToAvailability = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AssignServiceToAvailabilityPayload) =>
      assignServiceToAvailability(payload),
    onSuccess: () => {
      // Invalidate weekly schedule and availability services to refetch
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
      queryClient.invalidateQueries({ queryKey: ["availability-services"] });
    },
    onError: (error: Error) => {
      // Don't show toast here, let the calling component handle it
      throw error;
    },
  });
};

export const useAvailabilityServices = (availabilityId?: string) => {
  return useQuery<AvailabilityService[]>({
    queryKey: ["availability-services", availabilityId],
    queryFn: () => getAvailabilityServices(availabilityId),
    enabled: !!availabilityId && !availabilityId.includes("draft"), // Only fetch if availability ID exists and is not a draft
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

export const useUpdateAvailabilityService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      assignmentId,
      payload,
    }: {
      assignmentId: string;
      payload: UpdateAvailabilityServicePayload;
    }) => updateAvailabilityService(assignmentId, payload),
    onSuccess: () => {
      toast.success("Service updated successfully!");
      // Invalidate weekly schedule and availability services to refetch
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
      queryClient.invalidateQueries({ queryKey: ["availability-services"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update service");
    },
  });
};

export const useDeleteAvailabilityService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assignmentId: string) =>
      deleteAvailabilityService(assignmentId),
    onSuccess: () => {
      toast.success("Service removed successfully!");
      // Invalidate weekly schedule and availability services to refetch
      queryClient.invalidateQueries({ queryKey: ["weeklySchedule"] });
      queryClient.invalidateQueries({ queryKey: ["availability-services"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to remove service");
    },
  });
};

export const useDeleteDoctorService = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteDoctorService(id),
    onSuccess: () => {
      // Invalidate doctor services to refetch
      queryClient.invalidateQueries({ queryKey: ["calendarServices"] });
    },
    onError: (error: Error) => {
      // Don't show toast here, let the calling component handle it
      throw error;
    },
  });
};

export const useGetDoctorServices = () => {
  return useQuery<DoctorService[]>({
    queryKey: ["doctor-services"],
    queryFn: getDoctorServices,
    staleTime: 1000 * 60 * 2, // 2 minutes
    refetchOnWindowFocus: false,
  });
};

// Hook to fetch availability service pricing
export const useAvailabilityServicePricing = (
  doctorServiceAvailabilityId: string | undefined,
) => {
  return useQuery<AvailabilityServicePricingResponse>({
    queryKey: ["availabilityServicePricing", doctorServiceAvailabilityId],
    queryFn: () => getAvailabilityServicePricing(doctorServiceAvailabilityId!),
    enabled: !!doctorServiceAvailabilityId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

// Hook to fetch doctor service pricing (fallback)
export const useDoctorServicePricing = (
  serviceId: string | undefined,
  enabled: boolean = true,
) => {
  return useQuery<DoctorServicePricingResponse>({
    queryKey: ["doctorServicePricing", serviceId],
    queryFn: () => getDoctorServicePricing(serviceId!),
    enabled: !!serviceId && enabled,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

// Hook to create availability service pricing
export const useCreateAvailabilityServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAvailabilityServicePricingPayload) =>
      createAvailabilityServicePricing(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["availabilityServicePricing"],
      });
      queryClient.invalidateQueries({
        queryKey: ["availability-service-pricing"],
      });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    onError: (error: Error) => {
      toast.error(
        error.message || "Failed to create availability service pricing",
      );
    },
  });
};

// Hook to update availability service pricing
export const useUpdateAvailabilityServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      pricingId,
      payload,
    }: {
      pricingId: string;
      payload: UpdateAvailabilityServicePricingPayload;
    }) => updateAvailabilityServicePricing(pricingId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["availabilityServicePricing"],
      });
      queryClient.invalidateQueries({
        queryKey: ["availability-service-pricing"],
      });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    // No toast here — calling component handles errors with fallback logic
  });
};

// Hook to delete availability service pricing
export const useDeleteAvailabilityServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pricingId: string) =>
      deleteAvailabilityServicePricing(pricingId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["availability-service-pricing"],
      });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    // No toast here — calling component handles errors (pricing may not exist)
  });
};

// Hook to create doctor service pricing
export const useCreateDoctorServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateDoctorServicePricingPayload) =>
      createDoctorServicePricing(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctorServicePricing"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-service-pricing"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create doctor service pricing");
    },
  });
};

// Hook to update doctor service pricing
export const useUpdateDoctorServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      pricingId,
      payload,
    }: {
      pricingId: string;
      payload: UpdateDoctorServicePricingPayload;
    }) => updateDoctorServicePricing(pricingId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctorServicePricing"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-service-pricing"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    // No toast here — calling component handles errors with fallback logic
  });
};

// Hook to delete doctor service pricing
export const useDeleteDoctorServicePricing = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pricingId: string) => deleteDoctorServicePricing(pricingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctor-service-pricing"] });
      queryClient.invalidateQueries({ queryKey: ["doctor-availability"] });
    },
    // No toast here — calling component handles errors (pricing may not exist)
  });
};
