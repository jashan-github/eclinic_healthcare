// hooks/use-patient.ts
import { useQuery } from '@tanstack/react-query'
import { fetchPatientConditions } from '@/services/patients'
import { useParams } from '@tanstack/react-router'

export const usePatient = () => {
  const { patientId } = useParams({
    from: '/app/_app-layout/(common)/patients/_patient-layout/$patientId/medical-history/',
  })

  return useQuery({
    queryKey: ['patientConditions', patientId] as const,
    queryFn: fetchPatientConditions,
    enabled: !!patientId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })
}
