// src/features/app/locations/hooks/use-location.ts

import { useQuery } from "@tanstack/react-query"
import { getAllCountries, getCitiesByState, getStatesByCountry, type City, type Country, type State } from "../services/location-services"

export const useLocation = (countryId?: string, stateId?: string) => {
  const countriesQuery = useQuery<Country[], Error>({
    queryKey: ['countries'],
    queryFn: getAllCountries,
    staleTime: 1000 * 60 * 60, // 1 hour
  })

  const statesQuery = useQuery<State[], Error>({
    queryKey: ['states', countryId],
    queryFn: () => getStatesByCountry(countryId!),
    enabled: !!countryId,
    staleTime: 1000 * 60 * 10,
  })

  const citiesQuery = useQuery<City[], Error>({
    queryKey: ['cities', stateId],
    queryFn: () => getCitiesByState(stateId!),
    enabled: !!stateId,
    staleTime: 1000 * 60 * 10,
  })

  return {
    // Countries
    countries: countriesQuery.data || [],
    isLoadingCountries: countriesQuery.isLoading,
    countriesError: countriesQuery.error,

    // States
    states: statesQuery.data || [],
    isLoadingStates: statesQuery.isLoading,
    statesError: statesQuery.error,

    // Cities
    cities: citiesQuery.data || [],
    isLoadingCities: citiesQuery.isLoading,
    citiesError: citiesQuery.error,
  }
}
