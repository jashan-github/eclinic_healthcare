// patient-overview-content.tsx
import { type FC } from 'react'
import PatientOverviewPersonalDetails from './patient-overview-personal-details'

interface PatientOverviewContentProps {
  details: {
    fullName: string
    contactNumber: string
    email: string
    dateOfBirth: string
    emergencyContact: string
    familyContact: string
    bloodType: string
    maritalStatus: string
    occupation: string
    preferredLanguage: string
    address: string
  }
}

const PatientOverviewContent: FC<PatientOverviewContentProps> = ({ details }) => {
  return (
    <div className="p-6">
      <PatientOverviewPersonalDetails details={details} />
    </div>
  )
}

export default PatientOverviewContent