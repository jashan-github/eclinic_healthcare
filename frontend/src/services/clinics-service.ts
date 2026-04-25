// import axiosInstance from '@/lib/api'
import type { Clinic } from '@/types/clinic'

// Endpoint definitions
export const CLINICS_ENDPOINTS = {
  GET_CLINICS: '/v5/doctor/clinic/listing',
  GET_CLINIC_DETAILS: (clinicId: string) =>
    `/v5/doctor/clinic/listing?clinic_id=${clinicId}`,
  SWITCH_CLINIC: '/v5/doctor/clinic/switch',
  ASSIGN_CLINIC: '/v5/doctor/clinic/assign',
  CREATE_AND_ASSIGN_CLINIC: '/v5/doctor/clinic/createAndAssign',
  EDIT_CLINIC: (clinicId: string) => `/v5/doctor/clinic/${clinicId}/edit`,
  SAVE_CLINIC_TIMING: '/v5/doctor/clinic/saveClinicTiming'
} as const

// export const fetchAllAssociatedClinics = async (): Promise<Clinic[]> => {
//   try {
//     console.log("code came here")
//     const { data } = await axiosInstance.get(CLINICS_ENDPOINTS.GET_CLINICS)
//     return data.data
//   } catch (error) {
//     console.log(error)

//     throw error
//   }
// }

export const fetchAllAssociatedClinics = async (): Promise<Clinic[]> => {
  try {
    
    // Dummy data
    const dummyData: Clinic[] = [
      {
        id: "1",
        name: 'Test Clinic',
        c_id: null,
        timing: '',
        logo: '',
        email: null,
        phone_code: 0,
        phone: '',
        owner_name: '',
        health_services: [],
        fees: '',
        clinic_fee: {
          min: '',
          max: ''
        },
        isOwner: false,
        address: {
          address: '',
          latitude: '',
          longitude: '',
          country: '',
          state: '',
          city: ''
        },
        primary_address: {
          address: '',
          latitude: '',
          longitude: '',
          country: '',
          state: '',
          city: ''
        },
        other_address: [],
        amenities: [],
        specializations: [],
        connected_status: '',
        requestId: ''
      }
    ]
    
    return dummyData
    
    /* Original API call - commented out
    const { data } = await axiosInstance.get(CLINICS_ENDPOINTS.GET_CLINICS)
    return data.data
    */
  } catch (error) {
    console.log(error)
    throw error
  }
}