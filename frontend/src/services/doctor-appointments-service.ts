import axiosInstance from '@/lib/api'

export const DOCTOR_APPOINTMENTS = {
  GET_APPOINTMENT_LISTING: '/v3/doctor/appointment/listing',
  GET_TODAYS_APPOINTMENT_SIDEBAR: '/v3/doctor/appointment/listing',
  GET_ALL_PATIENTS: '/v3/doctor/getAllPatient',
  JOIN_VIDEO_CALL: (appointmentId: string) =>
    `/v3/doctor/appointment/join/${appointmentId}/videoCall`,
  END_VIDEO_CALL: (appointmentId: string) =>
    `/v3/doctor/appointment/end/${appointmentId}/videoCall`
} as const

export const doctorAppointmentsService = {
  getAppointmentListing: async () => {
    return axiosInstance.get(DOCTOR_APPOINTMENTS.GET_APPOINTMENT_LISTING)
  },
  getAllPatients: async () => {
    return axiosInstance.get(DOCTOR_APPOINTMENTS.GET_ALL_PATIENTS)
  },
  getTodaysAppointments: async () => {
    return axiosInstance.get(DOCTOR_APPOINTMENTS.GET_TODAYS_APPOINTMENT_SIDEBAR)
  },
  endVideoCall: async (appointmentId: string) => {
    return axiosInstance.get(DOCTOR_APPOINTMENTS.END_VIDEO_CALL(appointmentId))
  },
  joinVideoCall: async (appointmentId: string) => {
    return axiosInstance.get(DOCTOR_APPOINTMENTS.JOIN_VIDEO_CALL(appointmentId))
  }
}
