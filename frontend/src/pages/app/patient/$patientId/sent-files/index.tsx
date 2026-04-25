import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import SoapNotes from '@/components/e-clinic/doctor/patients/soap-notes/soap-notes'
import { useEffect, useRef, useState, type FC, type ReactElement } from 'react'
import { useParams } from '@tanstack/react-router'
import { usePatientAppointmentId } from '@/hooks/use-doctor-patients-list'

const SentFilesPage: FC = (): ReactElement => {
    const { patientId } = useParams({ strict: false })
    const { todayAppointmentId } = usePatientAppointmentId(patientId)
    console.log('Today Appointment ID from patient list:', todayAppointmentId)
    const containerRef = useRef<HTMLDivElement>(null)
    const [height, setHeight] = useState(0)
  
    // Debug: Log appointment ID from patient list API
    useEffect(() => {
      console.log('Patient ID:', patientId)
      console.log('Today Appointment ID from patient list:', todayAppointmentId)
    }, [patientId, todayAppointmentId])

    useEffect(() => {
      const updateHeight = () => {
        if (containerRef.current) {
          setHeight(containerRef.current.clientHeight)
        }
      }
  
      updateHeight()
      window.addEventListener('resize', updateHeight)
      return () => window.removeEventListener('resize', updateHeight)
    }, [])

  return (
    <div
      ref={containerRef}
      className="h-screen flex flex-col gap-4"
    >
      <div className="h-[60px] bg-white px-2 w-full">
        <div className="h-full w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="font-medium pl-2">
              <PatientHeader title="SOAP Notes" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col justify-between px-4 pb-4 flex-1">
        <div
          className="overflow-y-auto rounded-lg"
          style={{ maxHeight: `${height - 150}px` }}
        >
          <div
            className="bg-white rounded-lg p-6"
            style={{
              boxShadow: '6px 7px 20px 0px #0000001A',
            }}
          >
            <SoapNotes patientId={patientId} appointmentId={todayAppointmentId} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default SentFilesPage
