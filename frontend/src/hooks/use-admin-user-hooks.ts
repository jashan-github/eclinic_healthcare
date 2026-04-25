// src/hooks/use-admin-user-hooks.ts
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-toastify";
import {
  createUser,
  updateUser,
  deleteUser,
  fetchUsers,
  fetchUserStatistics,
  getUserById,
  type CreateUserPayload,
  type CreatedUserData,
  type UpdateUserPayload,
  type UpdatedUserData,
  type UsersResponse,
  type UserStatistics,
  type AdminUser,
} from "@/services/admin-user";

// Get All Users Hook
export const useUsers = (
  page: number = 1,
  perPage: number = 15,
  roleFilter?: "All" | "Doctor" | "Patient" | "Admin" | "super_admin" | "staff",
  searchTerm: string = "",
) => {
  const apiRole = (() => {
    if (!roleFilter || roleFilter === "All") return;
    if (roleFilter === "Doctor") return "doctor";
    if (roleFilter === "Patient") return "patient";
    if (roleFilter === "Admin") return "super_admin";
    if (roleFilter === "staff") return "staff";

    return;
  })();

  return useQuery<UsersResponse, Error>({
    queryKey: ["admin-users", page, perPage, apiRole, searchTerm],
    queryFn: () => fetchUsers(page, perPage, apiRole, searchTerm),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });
};

// Get User Statistics Hook
export const useUserStatistics = () => {
  return useQuery<UserStatistics, Error>({
    queryKey: ["admin-user-statistics"],
    queryFn: fetchUserStatistics,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });
};

// Get User by ID Hook
export const useUserById = (userId: string | null) => {
  return useQuery<AdminUser, Error>({
    queryKey: ["admin-user", userId],
    queryFn: () => getUserById(userId!),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  });
};

// Create User Hook
export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation<CreatedUserData, Error, CreateUserPayload>({
    mutationFn: createUser,
    onSuccess: (data) => {
      toast.success(`User "${data.name}" created successfully!`);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-statistics"] });
    },
    onError: (error) => {
      toast.error(error.message || "Unable to create user");
    },
  });
};

// Update User Hook
export const useUpdateUser = () => {
  const queryClient = useQueryClient();

  return useMutation<
    UpdatedUserData,
    Error,
    { userId: string; payload: UpdateUserPayload }
  >({
    mutationFn: ({ userId, payload }) => updateUser(userId, payload),
    onSuccess: (data) => {
      toast.success(`User "${data.name}" updated successfully!`);
      // Invalidate admin users
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-statistics"] });
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update user");
    },
  });
};

// Delete User Hook
export const useDeleteUser = () => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteUser,
    onSuccess: () => {
      toast.success("User deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-statistics"] });
    },
    onError: (error) => {
      toast.error(error.message || "Unable to delete user");
    },
  });
};
