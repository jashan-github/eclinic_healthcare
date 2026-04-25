import api, { type ApiResponse } from '@/lib/api-webinars'

export interface WebinarLivestreamCredentials {
  session_id: string
  channel_name: string
  token: string
  app_id: string
}

export interface WebinarWaitingRoomResponse {
  waiting_room: true
}

export type WebinarJoinResponse = WebinarLivestreamCredentials | WebinarWaitingRoomResponse

export const isWaitingRoom = (
  response: WebinarJoinResponse
): response is WebinarWaitingRoomResponse => {
  return 'waiting_room' in response && response.waiting_room === true
}

export const adminGoLiveWebinar = async (
  webinarId: string
): Promise<WebinarLivestreamCredentials> => {
  const response = await api.post<ApiResponse<WebinarLivestreamCredentials>>(
    `/v1/admin/webinars/${webinarId}/go-live`
  )
  return response.data.data
}

export const goLiveWebinar = async (
  webinarId: string
): Promise<WebinarLivestreamCredentials> => {
  const response = await api.post<ApiResponse<WebinarLivestreamCredentials>>(
    `/v1/doctor/webinars/${webinarId}/go-live`
  )
  return response.data.data
}

export const doctorJoinWebinar = async (
  webinarId: string
): Promise<WebinarJoinResponse> => {
  const response = await api.post<ApiResponse<WebinarJoinResponse>>(
    `/v1/doctor/webinars/${webinarId}/join`
  )
  return response.data.data
}

export const patientJoinWebinar = async (
  webinarId: string
): Promise<WebinarJoinResponse> => {
  const response = await api.post<ApiResponse<WebinarJoinResponse>>(
    `/v1/patient/webinars/${webinarId}/join`
  )
  return response.data.data
}
