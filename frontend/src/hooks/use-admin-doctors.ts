import { useQuery } from "@tanstack/react-query";
import {
  fetchAdminDoctors,
  type AdminDoctor,
} from "@/services/admin-doctors-service";

export const useAdminDoctors = (isActive: boolean = true, enabled = true) => {
  console.log(
    "useAdminDoctors called - enabled:",
    enabled,
    "isOpen prop:",
    enabled,
  );
  return useQuery<AdminDoctor[], Error>({
    queryKey: ["adminDoctors", isActive],
    queryFn: () => fetchAdminDoctors(isActive),
    enabled,
    staleTime: 1000 * 60 * 5,
    retry: 2,
  });
};
