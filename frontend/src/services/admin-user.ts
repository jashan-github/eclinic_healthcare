// src/services/admin-user.ts
import api from "@/lib/api";

// ==================== Interfaces ====================

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  role: "doctor" | "patient" | "staff" | "super_admin";
  status: boolean;
  is_active?: boolean;
  is_verified?: boolean;
  is_profile_complete?: boolean;
  clinic_id?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface MappedUser {
  id: string;
  name: string;
  email: string;
  contact: string;
  role: "Doctor" | "Patient" | "Staff" | "Admin";
  status: "Active" | "Inactive";
  initials: string;
}

export interface UsersResponse {
  users: AdminUser[];

  page: number;
  total_pages: number;
  per_page: number;
  total: number;
}

export interface UserStatistics {
  total: number;
  active: number;
  inactive: number;
  by_role: {
    doctor: number;
    patient: number;
    staff: number;
    admin: number;
  };
}

export interface CreateUserPayload {
  email: string;
  password: string;
  name: string;
  phone?: string;
  role: "doctor" | "patient" | "staff" | "super_admin";
  clinic_id?: string;
  is_active?: boolean;
  assigned_doctor_id?: string;
  // Doctor-specific fields
  education?: string;
  years_of_experience?: number;
  specializations?: string[];
}

export interface CreatedUserData {
  id: string;
  name: string;
  email: string;
  role: string;
  status: boolean;
  created_at: string;
  updated_at: string;
  [key: string]: any;
}

export interface CreateUserResponse {
  status: boolean;
  message: string;
  data: CreatedUserData;
}

export interface UpdateUserPayload {
  name?: string;
  email?: string;
  phone?: string;
  role?: "doctor" | "patient" | "staff" | "super_admin";
  is_active?: boolean;
  password?: string;
  clinic_id?: string;
  assigned_doctor_id?: string;
  // Doctor-specific fields
  education?: string;
  years_of_experience?: number;
  specializations?: string[];
}

export interface UpdatedUserData {
  id: string;
  name: string;
  email: string;
  role: string;
  status: boolean;
  updated_at: string;
  [key: string]: any;
}

// ==================== Service Functions ====================

// Get all users (with pagination)
// Add optional role param
export const fetchUsers = async (
  page: number = 1,
  perPage: number = 15,
  role?: "doctor" | "patient" | "super_admin" | "staff",
  searchTerm: string = "",
): Promise<UsersResponse> => {
  try {
    const params: Record<string, any> = {
      page,
      per_page: perPage,
      search: searchTerm,
    };

    if (role) {
      params.role = role;
    }

    const response = await api.get(`/v1/users`, { params });

    const apiData = response.data?.data || response.data || {};

    return {
      users: Array.isArray(apiData.users) ? apiData.users : [],
      page: apiData.page ?? page,
      total_pages: apiData.total_pages ?? 1,
      per_page: apiData.per_page ?? perPage,
      total: apiData.total ?? 0,
    };
  } catch (error) {
    console.error("Failed to fetch users:", error);
    throw new Error("Unable to load users data");
  }
};

// Get user statistics
export const fetchUserStatistics = async (): Promise<UserStatistics> => {
  try {
    const response = await api.get(`/v1/users/statistics`);
    return response.data.data || response.data;
  } catch (error) {
    console.error("Failed to fetch user statistics:", error);
    throw new Error("Unable to load user statistics");
  }
};

// Get user by ID
export const getUserById = async (userId: string): Promise<AdminUser> => {
  try {
    const response = await api.get(`/v1/users/${userId}`);
    return response.data.data || response.data;
  } catch (error) {
    console.error("Failed to fetch user:", error);
    throw new Error("Unable to load user data");
  }
};

// Create user
export const createUser = async (
  payload: CreateUserPayload,
): Promise<CreatedUserData> => {
  try {
    const response = await api.post<CreateUserResponse>("/v1/users", payload);

    return response.data.data || response.data;
  } catch (error: any) {
    console.error("Failed to create user:", error);

    const message =
      error?.response?.data?.message ||
      error?.response?.data?.errors?.[0] ||
      error?.message ||
      "Failed to create user";

    throw new Error(message);
  }
};

// Update user (PATCH)
export const updateUser = async (
  userId: string,
  payload: UpdateUserPayload,
): Promise<UpdatedUserData> => {
  try {
    const response = await api.patch<{
      status: boolean;
      message: string;
      data: UpdatedUserData;
    }>(`/v1/users/${userId}`, payload);

    return response.data.data || response.data;
  } catch (error: any) {
    const message =
      error?.response?.data?.message ||
      error?.message ||
      "Failed to update user";
    throw new Error(message);
  }
};

// Update user (PUT) - alternative method
export const updateUserPut = async (
  userId: string,
  payload: UpdateUserPayload,
): Promise<UpdatedUserData> => {
  try {
    const response = await api.put<{
      status: boolean;
      message: string;
      data: UpdatedUserData;
    }>(`/v1/users/${userId}`, payload);

    return response.data.data || response.data;
  } catch (error: any) {
    const message =
      error?.response?.data?.message ||
      error?.message ||
      "Failed to update user";
    throw new Error(message);
  }
};

// Delete user
export const deleteUser = async (userId: string): Promise<void> => {
  try {
    await api.delete(`/v1/users/${userId}`);
  } catch (error) {
    console.error("Failed to delete user:", error);
    throw new Error("Unable to delete user");
  }
};
