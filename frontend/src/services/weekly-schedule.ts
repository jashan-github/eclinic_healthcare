// src/services/weekly-schedule.ts
import api from '@/lib/api'

export interface WeeklySchedulePayload {
  weekdata: {
    day_name: string
    doctor_schedules: {
      id: string | null
      day_off: boolean
      start_time: string
      end_time: string
      appointment_services: {
        id: string
        service_name: string
      }[]
    }[]
  }[]
}

export interface WeeklyScheduleResponse {
  success: boolean
  message: string
  data?: any
}

// Create doctor availability payload
export interface CreateDoctorAvailabilityPayload {
  day_of_week: number
  start_time: string
  end_time: string
  is_active: boolean
  clinic_id?: string | null
}

// Update doctor availability payload
export interface UpdateDoctorAvailabilityPayload {
  day_of_week?: number
  start_time?: string
  end_time?: string
  is_active?: boolean
  clinic_id?: string | null
}

export interface CreateDoctorAvailabilityResponse {
  success: boolean
  message: string
  data?: {
    id: string
    [key: string]: any
  }
}

// Doctor Availability Response (from GET endpoint)
export interface DoctorAvailability {
  id: string
  doctor_id: string
  clinic_id: string
  day_of_week: number
  start_time: string
  end_time: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DoctorAvailabilityResponse {
  success: boolean
  message: string
  data: DoctorAvailability[]
  errors: Record<string, any>
}

// Map day of week number to day name (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
const dayOfWeekToDayName = (dayOfWeek: number): string => {
  const dayMap: Record<number, string> = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
  }
  return dayMap[dayOfWeek] ?? 'Monday'
}

// Map day name to day of week (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
const dayNameToDayOfWeek = (dayName: string): number => {
  const dayMap: Record<string, number> = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6
  }
  return dayMap[dayName] ?? 0 // Default to Monday (0) if not found
}

// Convert time from HH:mm to HH:mm:ss format (API expects time format, not ISO)
const convertTimeToTimeFormat = (time: string): string => {
  if (!time) {
    const now = new Date()
    return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:00`
  }
  // If already in HH:mm:ss format, return as is
  if (time.includes(':') && time.split(':').length === 3) {
    return time
  }
  // If in HH:mm format, add :00 for seconds
  if (time.includes(':') && time.split(':').length === 2) {
    return `${time}:00`
  }
  // Default fallback
  return `${time}:00`
}

// Get doctor availability
export const getDoctorAvailability = async (
  doctorId: string
): Promise<DoctorAvailabilityResponse> => {
  try {
    const response = await api.get<DoctorAvailabilityResponse>(
      `/v1/doctors/${doctorId}/availability`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch doctor availability:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to fetch availability'
    throw new Error(message)
  }
}

export const createDoctorAvailability = async (
  doctorId: string,
  payload: CreateDoctorAvailabilityPayload
): Promise<CreateDoctorAvailabilityResponse> => {
  try {
    const response = await api.post<CreateDoctorAvailabilityResponse>(
      `/v1/doctors/${doctorId}/availability`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to create doctor availability:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to create availability'
    throw new Error(message)
  }
}

// Update doctor availability
export interface UpdateDoctorAvailabilityResponse {
  success: boolean
  message: string
  data?: DoctorAvailability
  errors?: Record<string, any>
}

export const updateDoctorAvailability = async (
  availabilityId: string,
  payload: UpdateDoctorAvailabilityPayload
): Promise<UpdateDoctorAvailabilityResponse> => {
  try {
    const response = await api.put<UpdateDoctorAvailabilityResponse>(
      `/v1/availability/${availabilityId}`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update doctor availability:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to update availability'
    throw new Error(message)
  }
}

// Transform doctor availability data to ScheduleDay format
export const transformAvailabilityToScheduleDay = async (
  availabilityData: DoctorAvailability[]
): Promise<import('@/types/calendar').ScheduleDay[]> => {
  // Filter only active availabilities
  const activeAvailabilities = availabilityData.filter(avail => avail.is_active)
  
  // Fetch services for all availabilities in parallel
  const servicesPromises = activeAvailabilities.map(avail => 
    getAvailabilityServices(avail.id).catch(() => []) // Return empty array on error
  )
  const allServices = await Promise.all(servicesPromises)
  
  // Create a map of availability_id to services
  const servicesMap = new Map<string, AvailabilityService[]>()
  activeAvailabilities.forEach((avail, index) => {
    servicesMap.set(avail.id, allServices[index])
  })
  
  // Group by day_of_week
  const groupedByDay = activeAvailabilities.reduce((acc, avail) => {
    const dayName = dayOfWeekToDayName(avail.day_of_week)
    if (!acc[dayName]) {
      acc[dayName] = []
    }
    
    // Convert time format if needed (handle both HH:mm:ss and HH:mm)
    let startTime = avail.start_time
    let endTime = avail.end_time
    
    // If time is in HH:mm format, keep it as is (component expects HH:mm)
    if (startTime && startTime.split(':').length === 3) {
      startTime = startTime.substring(0, 5) // Convert HH:mm:ss to HH:mm
    }
    if (endTime && endTime.split(':').length === 3) {
      endTime = endTime.substring(0, 5) // Convert HH:mm:ss to HH:mm
    }
    
    // Get services for this availability
    const availabilityServices = servicesMap.get(avail.id) || []
    const mappedServices = availabilityServices.map((service): import('@/types/calendar').DoctorScheduleAppointmentService => ({
      id: service.service_id,
      service_name: service.service_name || 'Unknown Service',
      amount: 0, // Price not in response
      duration: service.slot_duration_minutes || 30,
      payment_mode: 'prepaid' as const
    }))
    
    acc[dayName].push({
      id: avail.id,
      day_name: dayName,
      start_time: startTime,
      end_time: endTime,
      day_off: 0, // is_active means not day off
      clinic: avail.clinic_id ? { id: avail.clinic_id, clinic_name: '', slot_type: '' } : null,
      appointment_services: mappedServices
    })
    return acc
  }, {} as Record<string, any[]>)

  // Convert to ScheduleDay array format
  return Object.entries(groupedByDay).map(([day_name, doctor_schedules]) => ({
    day_name,
    doctor_schedules
  }))
}

export const updateWeeklySchedule = async (
  payload: WeeklySchedulePayload
): Promise<WeeklyScheduleResponse> => {
  try {
    const response = await api.post<WeeklyScheduleResponse>(
      '/api/eclinic/v1/doctor/availability/weekly-schedule',
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update weekly schedule:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to save schedule'
    throw new Error(message)
  }
}

// Helper function to create availability payload from schedule data
export const buildCreateAvailabilityPayload = (
  dayName: string,
  startTime: string,
  endTime: string,
  clinicId?: string | null
): CreateDoctorAvailabilityPayload => {
  return {
    day_of_week: dayNameToDayOfWeek(dayName),
    start_time: convertTimeToTimeFormat(startTime),
    end_time: convertTimeToTimeFormat(endTime),
    is_active: true,
    clinic_id: clinicId || null
  }
}

// Helper function to build update availability payload
export const buildUpdateAvailabilityPayload = (
  dayName: string,
  startTime: string,
  endTime: string,
  clinicId?: string | null
): UpdateDoctorAvailabilityPayload => {
  return {
    day_of_week: dayNameToDayOfWeek(dayName),
    start_time: convertTimeToTimeFormat(startTime),
    end_time: convertTimeToTimeFormat(endTime),
    is_active: true,
    clinic_id: clinicId || null
  }
}

// Add service to doctor's offerings
export interface AddDoctorServicePayload {
  service_id: string
  slot_duration_minutes: number
}

export interface AddDoctorServiceResponse {
  success: boolean
  message: string
  data?: any
}

export const addDoctorService = async (
  payload: AddDoctorServicePayload
): Promise<AddDoctorServiceResponse> => {
  try {
    const response = await api.post<AddDoctorServiceResponse>(
      '/v1/doctor/services',
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to add doctor service:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to add service'
    throw new Error(message)
  }
}

export interface UpdateDoctorServicePayload {
  slot_duration_minutes?: number
  is_active?: boolean
}

export interface UpdateDoctorServiceResponse {
  success: boolean
  message: string
  data?: any
}

export const updateDoctorService = async (
  assignmentId: string,
  payload: UpdateDoctorServicePayload
): Promise<UpdateDoctorServiceResponse> => {
  try {
    const response = await api.patch<UpdateDoctorServiceResponse>(
      `/v1/doctor/services/${assignmentId}`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update doctor service:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to update doctor service'
    throw new Error(message)
  }
}

// Assign service to availability
export interface AssignServiceToAvailabilityPayload {
  availability_id: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  service_id: string
  slot_duration_minutes: number
}

export interface AssignServiceToAvailabilityResponse {
  success: boolean
  message: string
  data?: {
    id?: string
    [key: string]: any
  }
}

export const assignServiceToAvailability = async (
  payload: AssignServiceToAvailabilityPayload
): Promise<AssignServiceToAvailabilityResponse> => {
  try {
    const response = await api.post<AssignServiceToAvailabilityResponse>(
      '/v1/doctor/availability-services',
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to assign service to availability:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to assign service'
    throw new Error(message)
  }
}

// Get availability services
export interface AvailabilityService {
  id: string
  availability_id: string
  service_id: string
  consultation_mode: 'IN_CLINIC' | 'TELECONSULTATION'
  slot_duration_minutes: number
  created_at: string
  service_name: string
  service_mode: string
  availability_day: number
  availability_start_time: string
  availability_end_time: string
  [key: string]: any
}

export interface GetAvailabilityServicesResponse {
  success: boolean
  message: string
  data: AvailabilityService[]
  errors?: Record<string, any>
}

// Update availability service assignment
export interface UpdateAvailabilityServicePayload {
  consultation_mode?: 'IN_CLINIC' | 'TELECONSULTATION'
  slot_duration_minutes?: number
  payment_type?: 'PREPAID' | 'POSTPAID'
  advance_booking_days?: number
  minimum_notice_minutes?: number
  is_bookable?: boolean
  appointment_type?: 'REGULAR' | 'FOLLOWUP'
  follow_up_validity?: number
  nickname?: string
}

export interface UpdateAvailabilityServiceResponse {
  success: boolean
  message: string
  data?: any
}

export const updateAvailabilityService = async (
  assignmentId: string,
  payload: UpdateAvailabilityServicePayload
): Promise<UpdateAvailabilityServiceResponse> => {
  try {
    const response = await api.patch<UpdateAvailabilityServiceResponse>(
      `/v1/doctor/availability-services/${assignmentId}`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update availability service:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to update service assignment'
    throw new Error(message)
  }
}

// Delete availability service assignment
export interface DeleteAvailabilityServiceResponse {
  success: boolean
  message: string
  data?: any
}

export const deleteAvailabilityService = async (
  assignmentId: string
): Promise<DeleteAvailabilityServiceResponse> => {
  try {
    const response = await api.delete<DeleteAvailabilityServiceResponse>(
      `/v1/doctor/availability-services/${assignmentId}`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to delete availability service:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to delete service assignment'
    throw new Error(message)
  }
}

// Delete doctor service
export interface DeleteDoctorServiceResponse {
  success: boolean
  message: string
  data?: any
}

export const deleteDoctorService = async (
  id: string
): Promise<DeleteDoctorServiceResponse> => {
  try {
    const response = await api.delete<DeleteDoctorServiceResponse>(
      `/v1/doctor/services/${id}`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to delete doctor service:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to delete doctor service'
    throw new Error(message)
  }
}

// Get availability service pricing
export interface AvailabilityServicePricingItem {
  id?: string
  doctor_id?: string
  doctor_service_availability_id?: string
  service_id?: string
  service_name?: string
  service_mode?: string
  currency?: string
  price?: number
  price_amount?: number
  global_price?: number
  created_at?: string
  [key: string]: any
}

export interface AvailabilityServicePricingResponse {
  success: boolean
  message: string
  data?: AvailabilityServicePricingItem[] // API returns an array
  errors?: Record<string, any>
}

export const getAvailabilityServicePricing = async (
  doctorServiceAvailabilityId: string
): Promise<AvailabilityServicePricingResponse> => {
  try {
    const response = await api.get<AvailabilityServicePricingResponse>(
      `/v1/doctor/availability-service-pricing`,
      {
        params: {
          doctor_service_availability_id: doctorServiceAvailabilityId
        }
      }
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch availability service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to fetch availability service pricing'
    throw new Error(message)
  }
}

// Get doctor service pricing (fallback when availability pricing doesn't exist)
export interface DoctorServicePricingItem {
  id?: string
  doctor_id?: string
  service_id?: string
  service_name?: string
  service_mode?: string
  currency?: string
  price?: number
  price_amount?: number
  global_price?: number
  created_at?: string
  [key: string]: any
}

export interface DoctorServicePricingResponse {
  success: boolean
  message: string
  data?: DoctorServicePricingItem[] // API returns an array
  errors?: Record<string, any>
}

export const getDoctorServicePricing = async (
  serviceId: string
): Promise<DoctorServicePricingResponse> => {
  try {
    const response = await api.get<DoctorServicePricingResponse>(
      `/v1/doctor/service-pricing`,
      {
        params: {
          service_id: serviceId
        }
      }
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to fetch doctor service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to fetch doctor service pricing'
    throw new Error(message)
  }
}

// Create availability service pricing
export interface CreateAvailabilityServicePricingPayload {
  doctor_service_availability_id: string
  currency?: string
  price_amount: number
}

export interface CreateAvailabilityServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const createAvailabilityServicePricing = async (
  payload: CreateAvailabilityServicePricingPayload
): Promise<CreateAvailabilityServicePricingResponse> => {
  try {
    const response = await api.post<CreateAvailabilityServicePricingResponse>(
      `/v1/doctor/availability-service-pricing`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to create availability service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to create availability service pricing'
    throw new Error(message)
  }
}

// Update availability service pricing
export interface UpdateAvailabilityServicePricingPayload {
  price_amount?: number
  currency?: string
}

export interface UpdateAvailabilityServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const updateAvailabilityServicePricing = async (
  pricingId: string,
  payload: UpdateAvailabilityServicePricingPayload
): Promise<UpdateAvailabilityServicePricingResponse> => {
  try {
    const response = await api.patch<UpdateAvailabilityServicePricingResponse>(
      `/v1/doctor/availability-service-pricing/${pricingId}`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update availability service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to update availability service pricing'
    throw new Error(message)
  }
}

// Delete availability service pricing
export interface DeleteAvailabilityServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const deleteAvailabilityServicePricing = async (
  pricingId: string
): Promise<DeleteAvailabilityServicePricingResponse> => {
  try {
    const response = await api.delete<DeleteAvailabilityServicePricingResponse>(
      `/v1/doctor/availability-service-pricing/${pricingId}`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to delete availability service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to delete availability service pricing'
    throw new Error(message)
  }
}

// Create doctor service pricing
export interface CreateDoctorServicePricingPayload {
  service_id: string
  currency?: string
  price_amount: number
}

export interface CreateDoctorServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const createDoctorServicePricing = async (
  payload: CreateDoctorServicePricingPayload
): Promise<CreateDoctorServicePricingResponse> => {
  try {
    const response = await api.post<CreateDoctorServicePricingResponse>(
      `/v1/doctor/service-pricing`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to create doctor service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to create doctor service pricing'
    throw new Error(message)
  }
}

// Update doctor service pricing
export interface UpdateDoctorServicePricingPayload {
  price_amount?: number
  currency?: string
}

export interface UpdateDoctorServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const updateDoctorServicePricing = async (
  pricingId: string,
  payload: UpdateDoctorServicePricingPayload
): Promise<UpdateDoctorServicePricingResponse> => {
  try {
    const response = await api.patch<UpdateDoctorServicePricingResponse>(
      `/v1/doctor/service-pricing/${pricingId}`,
      payload
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to update doctor service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to update doctor service pricing'
    throw new Error(message)
  }
}

// Delete doctor service pricing
export interface DeleteDoctorServicePricingResponse {
  success: boolean
  message: string
  data?: any
}

export const deleteDoctorServicePricing = async (
  pricingId: string
): Promise<DeleteDoctorServicePricingResponse> => {
  try {
    const response = await api.delete<DeleteDoctorServicePricingResponse>(
      `/v1/doctor/service-pricing/${pricingId}`
    )
    return response.data
  } catch (error: any) {
    console.error('Failed to delete doctor service pricing:', error)
    const message =
      error?.response?.data?.message ||
      error?.message ||
      'Failed to delete doctor service pricing'
    throw new Error(message)
  }
}

export const getAvailabilityServices = async (
  availabilityId?: string
): Promise<AvailabilityService[]> => {
  try {
    const params = availabilityId ? { availability_id: availabilityId } : {}
    const response = await api.get<GetAvailabilityServicesResponse>(
      '/v1/doctor/availability-services',
      { params }
    )
    
    if (response.data?.success && Array.isArray(response.data.data)) {
      return response.data.data
    }
    
    return []
  } catch (error: any) {
    console.error('Failed to fetch availability services:', error)
    // Return empty array on error instead of throwing
    return []
  }
}

// Get doctor's services
export interface DoctorService {
  id: string
  doctor_id: string
  service_id: string
  clinic_id: string
  day_of_week: number | null
  day_name: string | null
  is_default: boolean
  slot_duration_minutes: number
  is_active: boolean
  created_at: string
  service_name: string
  service_mode: string
  appointment_type: string
  [key: string]: any
}

export interface GetDoctorServicesResponse {
  success: boolean
  message: string
  data: DoctorService[]
  errors?: Record<string, any>
}

export const getDoctorServices = async (): Promise<DoctorService[]> => {
  try {
    const response = await api.get<GetDoctorServicesResponse>(
      '/v1/doctor/services'
    )
    
    if (response.data?.success && Array.isArray(response.data.data)) {
      return response.data.data
    }
    
    return []
  } catch (error: any) {
    console.error('Failed to fetch doctor services:', error)
    return []
  }
}
