export type Clinic = {
  id: string
  clinic_name: string
  slot_type: string
  color_code?: string
}

export type DoctorScheduleAppointmentService = {
  id: string
  service_name: string
  amount: number | string
  duration: number | string
  payment_mode: 'prepaid' | 'postpaid'
  consultation_mode?: 'IN_CLINIC' | 'TELECONSULTATION'
  assignment_id?: string // Primary key id from availability-services API for updating/deleting
  doctor_service_id?: string // Primary key id from doctor-services API for deleting
  nickname?: string
  allow_patient_booking?: boolean
  advance_booking_days?: number
  minimum_notice_minutes?: number
  appointment_type?: 'regular' | 'followup'
  follow_up_validity?: number
}

export type DoctorSchedule = {
  id: string
  draft?: boolean
  day_name: string
  start_time: string | null
  end_time: string | null
  day_off: number
  clinic_id: string | null
  appointment_services: DoctorScheduleAppointmentService[]
}

export type ScheduleDay = {
  day_name: string
  doctor_schedules: DoctorSchedule[]
}

export type CalendarBlockItem = {
  id: string
  entire_day: boolean
  clinic_ids: string[]
  end_date: string
  end_time: string
  start_date: string
  start_time: string
}

export type CalendarBlockItemRaw = Omit<
  CalendarBlockItem,
  'id' | 'clinic_id' | 'entire_day'
>

// New time-off API types
export type TimeOffItem = {
  id: string
  clinic_id: string
  start_datetime: string
  end_datetime: string
  reason: string
  created_at?: string
  updated_at?: string
}

export type TimeOffPayload = {
  clinic_id: string
  start_datetime: string
  end_datetime: string
  reason: string
}

export type CalendarService = {
  id: string
  service_name: string
  book_ahead_days: number
  post_pay: boolean
  appointment_type: 'regular' | 'followup'
  currency: 'INR' | 'inr'
  mode: string[]
  archive: boolean
  owner_id: string
  service_id: number
  orvo_fee: number
  conv_fee: number
  pre_pay: boolean
  nickname: string
  allow_patient_booking: boolean
  price: number
  duration: number
  followup_validity: number
  book_before_mins: number
  conf_id: string
}

// Add these two interfaces at the bottom of calendar.ts

export interface AppointmentServiceDetail {
  id: string
  service_name: string
  nickname: string | null
  doctor_id: string
  appointment_treatment_id: string
  amount: number
  duration: number
  payment_method: string | null
  description?: string
  type: string
  hasAdvanceBooking?: number
  allow_patient_booking?: number
  advanceBookingFrom?: number
  minimum_notice?: number | null
  follow_up_validity?: number | null
  created_at: string
  updated_at: string
}

export interface CalendarServiceCategory {
  id: string
  name: string
  services: AppointmentServiceDetail[]
}