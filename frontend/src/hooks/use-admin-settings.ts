import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchAdminSettings,
  getNotificationSettings,
  getWaverNotificationSettings,
  updateAdminSettings,
  updateNotificationSettings,
  updateWaiverSettings,
  type AdminSettingsResponse,
  type UpdateAdminSettingsPayload,
  type UpdateNotificationSettingsPayload,
  type UpdateWaiverSettingsPayload,
} from "@/services/admin-settings-service";
import { toast } from "react-toastify";

export const useAdminSettings = () => {
  return useQuery<AdminSettingsResponse, Error>({
    queryKey: ["adminSettings"],
    queryFn: fetchAdminSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};
export const useAdminNotificationSettings = () => {
  return useQuery({
    queryKey: ["notificationSettings"],
    queryFn: getNotificationSettings,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
};

export const useUpdateNotificationSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateNotificationSettingsPayload) =>
      updateNotificationSettings(payload),

    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["notificationSettings"],
      });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message);
    },
  });
};
export const useAdminWaverNotificationSettings = () => {
  return useQuery({
    queryKey: ["admin-waiver-settings"],
    queryFn: getWaverNotificationSettings,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
};
export const useUpdateWaiverSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateWaiverSettingsPayload) =>
      updateWaiverSettings(payload),

    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: ["admin-waiver-settings"],
      });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.success(error.response?.data.message);
    },
  });
};
export const useUpdateAdminSettings = () => {
  const queryClient = useQueryClient();

  return useMutation<AdminSettingsResponse, Error, UpdateAdminSettingsPayload>({
    mutationFn: updateAdminSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminSettings"] });
      toast.success("Settings updated successfully!");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update settings");
    },
  });
};
