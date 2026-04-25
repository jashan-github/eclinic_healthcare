// rx-service.ts
import axiosInstance from '@/lib/api'

export const fetchRxPdf = async (
  patientId: string,
  soapNoteId: string,
  appointmentId: string,
  rxTemplateId: string
): Promise<Blob> => {
  try {
    const response = await axiosInstance.get(
      `/v1/doctor/patients/${patientId}/soap-notes/${soapNoteId}/pdf?appointment_id=${appointmentId}&rx_template_id=${rxTemplateId}`,
      {
        responseType: 'blob'
      }
    )

    return response.data
  } catch (error) {
    console.log(error)

    throw error
  }
}