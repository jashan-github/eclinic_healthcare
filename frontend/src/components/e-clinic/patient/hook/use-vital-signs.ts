// src/hooks/use-vital-signs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchVitalNames,
  fetchPatientVitalSigns,
  saveVitalSigns,
  type VitalName,
  type VitalSignsResponse,
  type VitalHistoryResponse,
  fetchPatientVitalHistory,
  updateVitalSignsConsent,
} from '../service/vital-signs-service';
import { toast } from 'react-toastify';

export const useVitalNames = () => {
  return useQuery<VitalName[], Error>({
    queryKey: ['vital-names'],
    queryFn: fetchVitalNames,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
};

export const usePatientVitalSigns = (patientId: string) => {
  return useQuery<VitalSignsResponse, Error>({
    queryKey: ['patient-vital-signs', patientId],
    queryFn: () => fetchPatientVitalSigns(patientId),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: !!patientId,
  });
};

export const useSaveVitalSigns = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: 
      | { vital_name_id: string; value: string | number }[]                     // old style
      | { vitals: { vital_name_id: string; value: string | number }[]; patientId?: string }   // new style
    ) => {
      if (Array.isArray(input)) {
        return saveVitalSigns(input);
      } else {
        return saveVitalSigns(input.vitals, input.patientId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patient-vital-signs'] });
    },
    onError: (error) => {
      console.error('Mutation error:', error);
    },
  });
};

export const usePatientVitalHistory = (patientId: string) => {
  return useQuery<VitalHistoryResponse, Error>({
    queryKey: ['patient-vital-history', patientId],
    queryFn: () => fetchPatientVitalHistory(patientId),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    enabled: !!patientId,
  });
};

export const useUpdateVitalConsent = () => {
  return useMutation({
    mutationFn: updateVitalSignsConsent,
    onSuccess: () => {
        toast.success("Consent Updated")
    },
    onError: (error) => {
        toast.error("Some error occurred")
      console.error('Consent update failed:', error);
    },
  });
};