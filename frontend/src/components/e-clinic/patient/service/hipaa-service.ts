// src/services/hipaa.ts
import api from '@/lib/api'

export interface HipaaReleaseFormPayload {
  section1_last_name: string
  section1_first_name: string
  section1_middle_name: string
  section1_date_of_birth: string
  section1_reference_number: string
  section1_address: string
  section1_country: string

  section2_name: string
  section2_address: string
  section2_country: string

  section3_name: string
  section3_relationship_to_patient: string
  section3_phone_number: string
  section3_address: string
  section3_country: string

  section4_expiration_date: string | null
  section4_expiration_event: string | null

  section5_medical_records: boolean
  section5_dental_records: boolean
  section5_other_non_specific: boolean
  section5_non_specific_records_details: string

  section6_communicable_disease: boolean
  section6_communicable_disease_date: string
  section6_communicable_disease_signature: string

  section6_reproductive_health: boolean
  section6_reproductive_health_date: string
  section6_reproductive_health_signature: string

  section6_hiv_test_results: boolean
  section6_hiv_test_results_date: string
  section6_hiv_test_results_signature: string

  section6_mental_health_records: boolean
  section6_mental_health_records_date: string
  section6_mental_health_records_signature: string

  section6_substance_use_disorder: boolean
  section6_substance_use_disorder_date: string
  section6_substance_use_disorder_signature: string

  section6_other: boolean
  section6_other_date: string
  section6_other_signature: string
  section6_other_records_details: string

  section6_psychotherapy_notes: boolean
  section6_psychotherapy_notes_date: string
  section6_psychotherapy_notes_signature: string

  section7_healthcare: boolean
  section7_research: boolean
  section7_marketing: boolean
  section7_sale: boolean
  section7_legal: boolean
  section7_other: boolean
  section7_other_details: string

  section9_additional_information: string | null

  section10_name_of_patient_client: string
  section10_signature_date: string
  section10_name_of_signatory_if_not_patient: string
  section10_authority_to_sign: string
  section10_name_of_translator: string
  section10_signature_of_translator: string
}

export interface HipaaReleaseFormResponse {
  id: string
  patient_id: string
  created_at: string
  updated_at: string
  status: string
  // Add other response fields as per your API
}

export const submitHipaaReleaseForm = async (
  payload: HipaaReleaseFormPayload
): Promise<HipaaReleaseFormResponse> => {
  try {
    const response = await api.post('/v1/patient/hipaa-release-forms', payload)
    return response.data
  } catch (error) {
    console.error('Failed to submit HIPAA release form:', error)
    throw new Error('Unable to submit HIPAA release form')
  }
}

export const fetchHipaaReleaseForms = async (): Promise<HipaaReleaseFormResponse[]> => {
  try {
    const response = await api.get('/v1/patient/hipaa-release-forms')
    return response.data
  } catch (error) {
    console.error('Failed to fetch HIPAA release forms:', error)
    throw new Error('Unable to load HIPAA release forms')
  }
}

export const fetchHipaaReleaseFormById = async (
  id: string
): Promise<HipaaReleaseFormResponse> => {
  try {
    const response = await api.get(`/v1/patient/hipaa-release-forms/${id}`)
    return response.data
  } catch (error) {
    console.error('Failed to fetch HIPAA release form:', error)
    throw new Error('Unable to load HIPAA release form')
  }
}