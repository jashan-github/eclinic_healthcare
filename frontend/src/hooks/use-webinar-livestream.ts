import { useMutation, useQuery } from '@tanstack/react-query'
import {
  adminGoLiveWebinar,
  goLiveWebinar,
  doctorJoinWebinar,
  patientJoinWebinar,
  type WebinarLivestreamCredentials,
  type WebinarJoinResponse,
} from '@/services/webinar-livestream-service'

export const useAdminGoLiveWebinar = () => {
  return useMutation<WebinarLivestreamCredentials, Error, string>({
    mutationFn: adminGoLiveWebinar,
  })
}

export const useGoLiveWebinar = () => {
  return useMutation<WebinarLivestreamCredentials, Error, string>({
    mutationFn: goLiveWebinar,
  })
}

export const useDoctorJoinWebinar = () => {
  return useMutation<WebinarJoinResponse, Error, string>({
    mutationFn: doctorJoinWebinar,
  })
}

export const usePatientJoinWebinar = () => {
  return useMutation<WebinarJoinResponse, Error, string>({
    mutationFn: patientJoinWebinar,
  })
}

export const useWebinarWaitingRoomPoll = (
  webinarId: string,
  role: 'admin' | 'doctor' | 'patient',
  enabled: boolean
) => {
  const joinFn = role === 'patient' ? patientJoinWebinar : doctorJoinWebinar

  return useQuery<WebinarJoinResponse, Error>({
    queryKey: ['webinar-waiting-room', webinarId, role],
    queryFn: () => joinFn(webinarId),
    enabled,
    refetchInterval: 5000,
    retry: 2,
  })
}
