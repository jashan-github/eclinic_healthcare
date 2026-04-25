// index.tsx
import { type FC, type ReactElement } from 'react'
import { useRef, useState, useEffect } from 'react'
import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import PatientMainContent from '@/components/e-clinic/doctor/patients/medical-history/patients-main-content'
import { useParams } from '@tanstack/react-router'

const MedicalHistory: FC = (): ReactElement => {
  const { patientId } = useParams({ strict: false })
  const containerRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)

  // Calculate container height for scroll area
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
      {/* Header */}
      <div className="h-[60px] bg-white px-2 w-full">
        <div className="h-full w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="font-medium pl-2">
              <PatientHeader title="Patient Medical History" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col justify-between px-4 pb-4 flex-1">
        {/* Scrollable Area */}
        <div
          className="overflow-y-auto"
          style={{ maxHeight: `${height - 150}px` }}
        >
          {/* Custom Shadow Card */}
          <div
            className="bg-white rounded-lg p-6"
            style={{
              boxShadow: '6px 7px 20px 0px #0000001A',
            }}
          >
            <PatientMainContent patientId={patientId} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default MedicalHistory