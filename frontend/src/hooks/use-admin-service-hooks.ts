// src/hooks/use-admin-service-hooks.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import {
  createAdminService,
  updateService,
  deleteService,
  fetchServices,
  type CreateAdminServicePayload,
  type CreatedAdminServiceData,
  type UpdateServicePayload,
  type UpdatedServiceData,
  type MappedService,
} from "@/services/admin-service";

// Create Admin Service Hook
export const useCreateAdminService = () => {
  const queryClient = useQueryClient();

  return useMutation<CreatedAdminServiceData, Error, CreateAdminServicePayload>(
    {
      mutationFn: createAdminService,
      onSuccess: (data) => {
        toast.success(`Service "${data.name}" created successfully!`);
        queryClient.invalidateQueries({ queryKey: ["admin-services"] });
        queryClient.invalidateQueries({ queryKey: ["adminServices"] });
        queryClient.invalidateQueries({ queryKey: ["services"] });
      },
      onError: (error) => {
        toast.error(error.message || "Unable to create service");
      },
    },
  );
};

// Update Admin Service Hook
export const useUpdateAdminService = () => {
  const queryClient = useQueryClient();

  return useMutation<
    UpdatedServiceData,
    Error,
    {
      serviceId: string;
      payload: UpdateServicePayload;
      clinicId?: string;
      serviceName?: string;
    }
  >({
    mutationFn: ({ serviceId, payload, clinicId, serviceName }) =>
      updateService(serviceId, payload, clinicId, serviceName),
    onSuccess: (data) => {
      toast.success(`Service "${data.service_name}" updated successfully!`);
      // Invalidate admin services
      queryClient.invalidateQueries({ queryKey: ["admin-services"] });
      queryClient.invalidateQueries({ queryKey: ["adminServices"] });
      // Invalidate individual service query
      queryClient.invalidateQueries({ queryKey: ["service"] });
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update service");
    },
  });
};

// Delete Admin Service Hook
export const useDeleteAdminService = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteService,
    onSuccess: () => {
      toast.success("Service deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["admin-services"] });
      queryClient.invalidateQueries({ queryKey: ["adminServices"] });
      queryClient.invalidateQueries({ queryKey: ["services"] });
    },
    onError: (error) => {
      toast.error(error.message || "Unable to delete service");
    },
  });
};

// Get All Admin Services Hook
export const useServices = (options?: { enabled?: boolean }) => {
  return useQuery<MappedService[], Error>({
    queryKey: ["admin-services"],
    queryFn: fetchServices,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: false, // Don't retry on 403 errors
    enabled: options?.enabled !== false, // Fetch by default, unless explicitly disabled
  });
};
