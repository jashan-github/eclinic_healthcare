// src/features/app/locations/services/location-service.ts
import axiosInstance from '@/lib/api'

// Types
export interface Country {
  id: string
  shortname: string
  name: string
  phonecode: number
  created_at: string
  updated_at: string
  deleted_at: string | null
}

export interface State {
  id: string
  name: string
  icon: string
  sortcode: string
  country_id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  state_id: string | null
}

export interface City {
  id: string
  name: string
  icon: string
  state_id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  city_id: string | null
}

// 1. Get all countries
export const getAllCountries = async (): Promise<Country[]> => {
  try {
    const { data } = await axiosInstance.get('/v1/locations/countries')
    return { data }.data.data.countries
  } catch (error) {
    console.error('Failed to fetch countries:', error)
    throw error
  }
}

// 2. Get states by country_id
export const getStatesByCountry = async (countryId: string): Promise<State[]> => {
  if (!countryId) return []
  try {
    const { data } = await axiosInstance.get(`/v1/locations/countries/${countryId}/states`)
    return { data }.data.data.states
  } catch (error) {
    console.error('Failed to fetch states:', error)
    throw error
  }
}

// 3. Get cities by state_id
export const getCitiesByState = async (stateId: string): Promise<City[]> => {
  if (!stateId) return []
  try {
    const { data } = await axiosInstance.get(`/v1/locations/states/${stateId}/cities`)
    return { data }.data.data.cities
  } catch (error) {
    console.error('Failed to fetch cities:', error)
    throw error
  }
}
