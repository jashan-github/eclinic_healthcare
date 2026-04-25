import { useQuery } from '@tanstack/react-query'
import { fetchPatientPersonalDetails } from '@/services/patients'
import { useParams } from '@tanstack/react-router'

export const usePatientDetails = () => {
  const { patientId } = useParams({
    from: '/app/_app-layout/(common)/patients/_patient-layout/$patientId/patient-overview/',
  })

  return useQuery({
    queryKey: ['patientDetails', patientId] as const,
    queryFn: fetchPatientPersonalDetails,
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })
}