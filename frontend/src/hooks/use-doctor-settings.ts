// src/hooks/use-doctor-settings.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchFees,
  fetchStaffRestrictions,
  updateFeeService,
  updateStaffRestrictions,
  type FeeService,
  type FeeServiceUpdate,
  type StaffRestrictionsData,
} from '@/services/doctor-settings-service'

export const useStaffRestrictions = () => {
  return useQuery<StaffRestrictionsData, Error>({
    queryKey: ['doctor-staff-restrictions'],
    queryFn: fetchStaffRestrictions,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useUpdateStaffRestrictions = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateStaffRestrictions,
    onSuccess: (data) => {
      queryClient.setQueryData(['doctor-staff-restrictions'], data)
      queryClient.invalidateQueries({ queryKey: ['doctor-staff-restrictions'] })
    },
  })
}

export const useFees = () => {
  return useQuery<FeeService[], Error>({
    queryKey: ['doctor-fees'],
    queryFn: fetchFees,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
  })
}

export const useUpdateFee = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FeeServiceUpdate }) => updateFeeService(id, data),
    onSuccess: (updatedService) => {
      queryClient.setQueryData(['doctor-fees'], (old: FeeService[] = []) =>
        old.map(s => (s.id === updatedService.id ? updatedService : s))
      )
    },
  })
}
