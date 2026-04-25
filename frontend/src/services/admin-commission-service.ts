import api from "@/lib/api";

export type UpsertCommissionPayload = {
  rate: number;
  status: "ACTIVE" | "INACTIVE";
};

export type CommissionRangeParams = {
  date_from?: string;
  date_to?: string;
};
export const getCommissions = async () => {
  try {
    const { data } = await api.get("/v1/admin/service-commissions");
    return data.data;
  } catch (error) {
    console.error(error);
    throw new Error("Unable to fetch comissions");
  }
};

export const getCommissionByService = async (serviceId: string) => {
  const res = await api.get(`/v1/admin/services/${serviceId}/commission`);
  return res.data.data;
};

export const getCommissionsByServiceRange = async (
  params?: CommissionRangeParams,
) => {
  const response = await api.get("/v1/admin/service-commissions/by-service", {
    params,
  });

  return response.data.data;
};

export const upsertServiceCommission = async (
  serviceId: string,
  payload: UpsertCommissionPayload,
) => {
  const response = await api.put(
    `/v1/admin/services/${serviceId}/commission`,
    payload,
  );

  return response.data;
};

export const deletCommission = async (serviceId: string) => {
  try {
    const response = await api.delete(
      `/v1/admin/services/${serviceId}/commission`,
    );
    return response.data;
  } catch (error) {
    console.error(error);
    throw new Error("Unable to fetch comissions");
  }
};
export const getCommissionsStats = async () => {
  try {
    const response = await api.get(`/v1/admin/service-commissions/stats`);
    return response.data;
  } catch (error) {
    console.error(error);
    throw new Error("Unable to fetch comissions");
  }
};
