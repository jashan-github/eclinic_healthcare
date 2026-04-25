// src/hooks/use-medical-services-hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getMedicalServices,
  getMedicalServiceById,
  createMedicalService,
  updateMedicalService,
  deleteMedicalService,
} from '../service/medical-services-service';
import type { MedicalServiceResponse } from '../service/medical-services-service';

export function useMedicalServices(status?: boolean) {
  return useQuery<MedicalServiceResponse[]>({
    queryKey: ['medical-services', status],
    queryFn: () => getMedicalServices(status),
  });
}

export function useMedicalServiceById(id: string | null) {
  return useQuery<MedicalServiceResponse>({
    queryKey: ['medical-service', id],
    queryFn: () => getMedicalServiceById(id!),
    staleTime: 0,
    enabled: !!id,
  });
}

export function useCreateMedicalService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createMedicalService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medical-services'] });
    },
  });
}

export function useUpdateMedicalService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateMedicalService(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medical-services'] });
    },
  });
}

export function useDeleteMedicalService() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteMedicalService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medical-services'] });
    },
  });
}
