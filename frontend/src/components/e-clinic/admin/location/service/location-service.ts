// src/services/location-service.ts
import api, { type ApiResponse } from '@/lib/api'

export interface Location {
  id: string
  name: string
  branch_type: string
  address: string
  building_name: string | null
  street_name: string | null
  pincode: string | null
  phone: string | null
  email: string | null
  country: string
  state: string
  city: string
  country_id: string
  state_id: string
  city_id: string
  latitude: number | null
  longitude: number | null
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface LocationsResponse {
  locations: Location[]
}

// GET: Fetch all clinic locations
export const fetchLocations = async (): Promise<LocationsResponse> => {
  try {
    const response = await api.get<ApiResponse<LocationsResponse>>(
      '/v1/admin/clinic-locations'
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to fetch locations')
    }

    return response.data.data
  } catch (error) {
    console.error('Failed to fetch locations:', error)
    throw new Error('Unable to load locations data')
  }
}

// GET: Fetch a specific clinic location by ID
export const fetchLocationById = async (locationId: string): Promise<Location> => {
  try {
    const response = await api.get<ApiResponse<{ location: Location }>>(
      `/v1/admin/clinic-locations/${locationId}`
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to fetch location')
    }

    return response.data.data.location
  } catch (error) {
    console.error('Failed to fetch location:', error)
    throw new Error('Unable to load location data')
  }
}

// POST: Create a new clinic location
export const createLocation = async (
  payload: {
    name: string
    branch_type: string
    address: string
    country_id: string
    state_id: string
    city_id: string
    phone?: string
    email?: string
    is_primary: boolean
  }
): Promise<Location> => {
  try {
    const response = await api.post<ApiResponse<{ location: Location }>>(
      '/v1/admin/clinic-locations',
      payload
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to create location')
    }

    return response.data.data.location
  } catch (error) {
    console.error('Failed to create location:', error)
    throw new Error('Unable to create location')
  }
}

// PUT: Update a clinic location
export const updateLocation = async (
  locationId: string,
  payload: {
    name?: string
    branch_type?: string
    address?: string
    country_id?: string
    state_id?: string
    city_id?: string
    phone?: string
    email?: string
    is_primary?: boolean
  }
): Promise<Location> => {
  try {
    const response = await api.put<ApiResponse<{ location: Location }>>(
      `/v1/admin/clinic-locations/${locationId}`,
      payload
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to update location')
    }

    return response.data.data.location
  } catch (error) {
    console.error('Failed to update location:', error)
    throw new Error('Unable to update location')
  }
}

// DELETE: Delete a clinic location
export const deleteLocation = async (locationId: string): Promise<void> => {
  try {
    const response = await api.delete<ApiResponse<null>>(
      `/v1/admin/clinic-locations/${locationId}`
    )

    if (!response.data.status) {
      throw new Error(response.data.message || 'Failed to delete location')
    }
  } catch (error) {
    console.error('Failed to delete location:', error)
    throw new Error('Unable to delete location')
  }
}