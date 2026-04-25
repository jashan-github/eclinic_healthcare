// src/hooks/use-clinics.ts

import { fetchClinics, type ClinicsResponse, type ClinicLocation } from '@/services/doctor-template-clinic'
import { useQuery } from '@tanstack/react-query'

export interface ClinicsTransformed {
  locations: ClinicLocation[]
  primaryLocation: ClinicLocation | undefined
}

export const useClinics = () => {
  return useQuery<ClinicsResponse, Error, ClinicsTransformed>({
    queryKey: ['clinic-locations'],
    queryFn: fetchClinics,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: 2,
    select: (data) => ({
      locations: data.data.locations,
      primaryLocation: data.data.locations.find(c => c.is_primary) || data.data.locations[0],
    }),
  })
}