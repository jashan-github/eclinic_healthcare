import {
  deletCommission,
  getCommissionByService,
  getCommissions,
  getCommissionsByServiceRange,
  getCommissionsStats,
  upsertServiceCommission,
  type CommissionRangeParams,
} from "@/services/admin-commission-service";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";

export const useGetCommissions = () => {
  return useQuery({
    queryKey: ["commission"],
    queryFn: getCommissions,
  });
};

export const useGetCommissionsStats = () => {
  return useQuery({
    queryKey: ["commission-stats"],
    queryFn: getCommissionsStats,
  });
};

export const useGetCommissionByService = (
  serviceId: string | null,
  enabled: boolean,
) =>
  useQuery({
    queryKey: ["commission", serviceId],
    queryFn: () => getCommissionByService(serviceId!),
    enabled: enabled && !!serviceId,
  });

export const useUpsertCommission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      serviceId,
      rate,
      status,
    }: {
      serviceId: string;
      rate: number;
      status?: "ACTIVE" | "INACTIVE";
    }) =>
      upsertServiceCommission(serviceId, {
        rate,
        status: status ?? "ACTIVE",
      }),

    onSuccess: (data) => {
      toast.success(data?.message);
      queryClient.invalidateQueries({
        queryKey: ["commission"],
      });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.message);
    },
  });
};

export const useDeleteCommission = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (serviceId: string) => deletCommission(serviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["commission"],
      });
      toast.success("Deleted successfully");
    },
    onError: () => {
      toast.error("Error deleting Comission");
    },
  });
};

export const useGetCommissionByDateRange = (params?: CommissionRangeParams) => {
  return useQuery({
    queryKey: ["commission-by-service", params?.date_from, params?.date_to],
    queryFn: () => getCommissionsByServiceRange(params),
  });
};
