import { useQuery } from '@tanstack/react-query'
import { fetchDoctorPatientsList, type PatientsListResponse } from '@/services/doctor-patients-list-service'

export const useDoctorPatientsList = (params?: { page?: number; per_page?: number }) => {
  return useQuery<PatientsListResponse, Error>({
    queryKey: ['doctorPatientsList', params],
    queryFn: () => fetchDoctorPatientsList(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}

// Hook to get today_appointment_id for a specific patient
export const usePatientAppointmentId = (patientId: string | undefined) => {
  const { data } = useDoctorPatientsList({ per_page: 100 })
  
  const patient = data?.data?.patients?.find(p => p.id === patientId)
  
  return {
    todayAppointmentId: patient?.today_appointment_id || undefined,
    patient
  }
}

