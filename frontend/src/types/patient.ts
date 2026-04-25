import type { MedicalHistory } from './medical-history'

export type Patient = {
  id?: string
  uhid?: string
  name: string
  first_name: string
  last_name: string
  country_code: string
  patient_id?: string
  phone: string
  phone_number?: string
  age: number | string
  date_of_birth: string
  contact?: number
  gender: string
  address: string
  landmark: string
  city: string
  pincode: string
  last_visited: string
  follow_up: string
  username: string // This will be the UHID for each patient
  medical_history: string
}

export type PatientMedicalHistoryResponse = {
  categories: MedicalHistory[]
  is_medical_history: boolean
}

export type PatientMedicalHistoryPayload = {
  medical_history_data: MedicalHistory[]
  is_medical_history: boolean
}

export type PatientOptionalFieldName =
  | 'phone'
  | 'salutation'
  | 'first_name'
  | 'middle_name'
  | 'last_name'
  | 'age'
  | 'dob'
  | 'gender'
  | 'uhid'
  | 'address'
  | 'city'
  | 'pincode'
  | 'relationship_with_patient'
  | 'blood_group'
  | 'referred_by_doctor'
  | 'alternate_phone_number'
  | 'occupation'
  | 'name_of_informant'
  | 'channel'
  | 'religion'
  | 'marital_status'
  | 'preferred_language'
  | 'email'

export type PatientConfigurationField = {
  name: PatientOptionalFieldName
  label: string
  selected: boolean
}

export type PatientVisitDate = {
  date: string
  day: string
  day_name: string
  month_name: string
  month: string
  year: string
}

export type PatientVisit = {
  id: string
  title: string
  appointment_created_at: string
  appointment_start_time: string
  appointment_end_time: string | null
  check_status: string
  bookingId: string
  device_type: string | null
  notes: string
  precription_pdf_url: string | null
  digital_precription_pdf_url: string | null
  video_call_recordings: string[]
  assessment_summary: string | null
  appointment_date: PatientVisitDate
}
