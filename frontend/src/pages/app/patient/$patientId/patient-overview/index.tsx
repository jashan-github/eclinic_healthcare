// index.tsx
import { type FC, type ReactElement } from 'react'
import { useRef, useState, useEffect } from 'react'
import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import PatientOverviewContent from '@/components/e-clinic/doctor/patients/patient-overview/patient-overview-content'
import PatientOverviewHealth from '@/components/e-clinic/doctor/patients/patient-overview/patient-overview-health'
import GlobalLoader from '@/components/orvo/common/global-loader'
import { useDoctorPatientDetails } from '@/hooks/use-doctor-patient-details'
import { useParams } from '@tanstack/react-router'

const PatientOverview: FC = (): ReactElement => {
  const { patientId } = useParams({ strict: false })
  const containerRef = useRef<HTMLDivElement>(null)
  const [height, setHeight] = useState(0)

  const { data: patient, isLoading, error } = useDoctorPatientDetails(patientId)

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

  if (isLoading) return <GlobalLoader />
  if (error || !patient) return <div className="text-red-600 text-center py-8">Failed to load patient data</div>

  // Transform once here
  const personalDetails = {
    fullName: patient.name,
    contactNumber: patient.phone_number || 'Not provided',
    email: patient.email || 'Not provided',
    dateOfBirth: patient.date_of_birth
      ? (() => {
          const [d, m, y] = patient.date_of_birth.split('-')
          const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
          return `${d} ${months[parseInt(m) - 1]} ${y}`
        })()
      : 'Not provided',
    emergencyContact: patient.emergency_contact_number || 'Not provided',
    familyContact: patient.family_contact_number || 'Not provided',
    bloodType: patient.blood_type || 'Not provided',
    maritalStatus: patient.marital_status || 'Not provided',
    occupation: patient.occupation || 'Not provided',
    preferredLanguage: patient.preferred_language || 'Not provided',
    address: patient.address || 'Not provided',
  }

  return (
    <div ref={containerRef} className="h-screen flex flex-col gap-4">
      {/* Header */}
      <div className="h-[60px] bg-white px-2 w-full">
        <div className="h-full w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="font-medium pl-2">
              <PatientHeader title="Patient Overview" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-col justify-between px-4 pb-4 flex-1">
        <div className="overflow-y-auto" style={{ maxHeight: `${height - 150}px` }}>
          <div className="space-y-4 p-1">
            {/* Card 1 */}
            <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4">
              <PatientOverviewContent details={personalDetails} />
            </div>

            <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4">
              <PatientOverviewHealth patient={patient} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PatientOverview