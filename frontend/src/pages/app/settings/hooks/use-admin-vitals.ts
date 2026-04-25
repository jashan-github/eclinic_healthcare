// src/hooks/use-admin-vitals-hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getVitals,
  getVitalById,
  createVital,
  updateVital,
  deleteVital,
  reorderVitals,
} from '../service/admin-vitals-service';
import type { VitalResponse } from '../service/admin-vitals-service';

export function useVitals() {
  return useQuery<VitalResponse[]>({
    queryKey: ['vitals'],
    queryFn: getVitals,
  });
}

export function useVitalById(id: string | null) {
  return useQuery<VitalResponse>({
    queryKey: ['vital', id],
    queryFn: () => getVitalById(id!),
    staleTime: 0,
    enabled: !!id,
  });
}

export function useCreateVital() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createVital,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vitals'] });
    },
  });
}

export function useUpdateVital() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateVital(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vitals'] });
    },
  });
}

export function useDeleteVital() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteVital,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vitals'] });
    },
  });
}

export function useReorderVitals() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: reorderVitals,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vitals'] });
    },
  });
}