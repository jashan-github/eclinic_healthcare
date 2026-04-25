import {
  fetchPermissions,
  updatePermissions,
} from "@/services/admin-permisson-services";
import { useQuery } from "@tanstack/react-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { toast } from "react-toastify";

interface ApiError {
  message: string;
}

export const useAdminPermissionServices = () => {
  return useQuery({
    queryKey: ["adminPermissions"],
    queryFn: fetchPermissions,
  });
};
export const useUpdatePermissions = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updatePermissions,
    onSuccess: () => {
      toast.success("Permissions updated successfully");
      queryClient.invalidateQueries({ queryKey: ["adminPermissions"] });
    },
    onError: (error: AxiosError<ApiError>) => {
      toast.error(error.response?.data?.message ?? "Something went wrong");
    },
  });
};
