import { useEffect, useRef, useState, type FC, type ReactElement } from 'react'
import MedicalDocumentsCard from '@/components/e-clinic/doctor/patients/medical-documents/medical-documents-card'
import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import { useParams } from '@tanstack/react-router'

const PatientMedicalCertificates: FC = (): ReactElement => {
  const { patientId } = useParams({ strict: false })
  const containerRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)

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
              <PatientHeader title="Medical Documents" />
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col justify-between px-4 pb-4 flex-1">
        <div
          className="overflow-y-auto"
          style={{ maxHeight: `${height - 150}px` }}
        >
          <div
            className="bg-white rounded-lg p-6"
            style={{
              boxShadow: '6px 7px 20px 0px #0000001A',
            }}
          >
            <MedicalDocumentsCard patientId={patientId} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default PatientMedicalCertificates
