import type { PatientReferral } from '@/types/patient-referral'
import { getAllPatientReferrals } from '../services/patient-referral-service'
import { useSuspenseQuery } from '@tanstack/react-query'

export const usePatientReferrals = () => {
  // Fetch All Patient Referrals information
  const {
    data: patientReferrals,
    isLoading,
    error
  } = useSuspenseQuery<PatientReferral[], Error>({
    queryKey: ['myPatientReferrals'],
    queryFn: getAllPatientReferrals,
    staleTime: 1000 * 60 * 5 // 5 minutes
  })

  return {
    patientReferrals: patientReferrals || [],
    isLoading,
    error
  }
}
