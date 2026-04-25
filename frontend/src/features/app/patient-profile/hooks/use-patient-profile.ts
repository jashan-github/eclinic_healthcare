import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getPatientProfileDetails,
  updatePatientProfile,
} from "../services/patient-profile-service";
import type {
  PatientProfile,
  UpdatePatientProfilePayload,
} from "../services/patient-profile-service";

export const usePatientProfile = () => {
  const queryClient = useQueryClient();

  const {
    data: patientProfile,
    isLoading,
    error,
  } = useQuery<PatientProfile, Error>({
    queryKey: ["patientProfileDetails"],
    queryFn: getPatientProfileDetails,
    staleTime: 1000 * 60 * 5,
    retry: 1,
  });

  const updateMutation = useMutation({
    mutationFn: updatePatientProfile,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["patientProfileDetails"],
      });
      // Also invalidate patient personal info for header dropdown
      await queryClient.invalidateQueries({
        queryKey: ["patientPersonalInfo"],
      });
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] });
    },
  });

  return {
    patientProfile: patientProfile || null,
    isLoading,
    error,
    updateProfile: (
      payload: UpdatePatientProfilePayload,
      options?: { onSuccess?: () => void; onError?: (error: any) => void },
    ) => {
      updateMutation.mutate(payload, {
        onSuccess: () => {
          options?.onSuccess?.();
        },
        onError: (error) => {
          options?.onError?.(error);
        },
      });
    },
    updateProfileAsync: updateMutation.mutateAsync,
    isUpdatingProfile: updateMutation.isPending,
  };
};
