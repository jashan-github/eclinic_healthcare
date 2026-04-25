import api from "@/lib/api";

export const fetchPermissions = async () => {
  try {
    const response = await api.get("/v1/admin/role-permissions");
    return response.data.data;
  } catch (error) {
    console.error("Failed to fetch service:", error);
    throw new Error("Unable to load service data");
  }
};
export const updatePermissions = async (payload: any) => {
  const res = await api.put("/v1/admin/role-permissions", payload);
  return res.data;
};
