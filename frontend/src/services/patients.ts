// services/patients.ts
// import axiosInstance from '@/lib/api'

import { type QueryFunctionContext } from '@tanstack/react-query'

export interface PatientCondition {
  label: string
  isActive: boolean
  years?: string | null
}
export interface PatientPersonalDetails {
  fullName: string
  contactNumber: string
  email: string
  dateOfBirth: string
  emergencyContact: string
  familyContact: string
  bloodType: string
  maritalStatus: string
  occupation: string
  preferredLanguage: string
  address: string
  allergies: string
}

const mockPersonalDetails: PatientPersonalDetails = {
  fullName: 'Nick Williams',
  contactNumber: '+1234567890',
  email: 'nickwill@gmail.com',
  dateOfBirth: '10-03-1984',
  emergencyContact: '+1234567890',
  familyContact: '+1234567890',
  bloodType: 'O+',
  maritalStatus: 'Married',
  occupation: 'Teacher',
  preferredLanguage: 'English, Spanish',
  address: '123 Oak Street, Anytown, CA 90210',
  allergies: 'Dust Mites'
}

const mockPatientConditions: PatientCondition[] = [
  { label: 'Diabetes mellitus', isActive: true, years: '5 Years' },
  { label: 'Hypertension', isActive: false },
  { label: 'Hypothyroidism', isActive: false },
  { label: 'Alcohol', isActive: false },
  { label: 'Tobacco', isActive: false },
  { label: 'Smoke', isActive: false },
]

export const fetchPatientConditions = async (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _ctx: QueryFunctionContext<readonly ['patientConditions', string]>
): Promise<PatientCondition[]> => {
  // TODO(backend): wire to real endpoint when ready.
  // const [, patientId] = _ctx.queryKey
  // const { data } = await axiosInstance.get(`v5/doctor/patient/${patientId}/history`)
  // return data.data
  try {
    return mockPatientConditions
  } catch (error) {
    console.error('Failed to fetch patient history:', error)
    throw error
  }
}

export const fetchPatientPersonalDetails = async (
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _ctx: QueryFunctionContext<readonly ['patientDetails', string]>
): Promise<PatientPersonalDetails> => {
  // const [, patientId] = queryKey

  try {
    // const { data } = await axiosInstance.get(
    //   `v5/doctor/patient/${patientId}/personal-details`
    // )
    // return data

    return mockPersonalDetails
  } catch (error) {
    console.error('Failed to fetch patient details:', error)
    throw error
  }
}