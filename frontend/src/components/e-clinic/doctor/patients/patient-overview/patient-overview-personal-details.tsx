// patient-overview-personal-details.tsx
import { type FC } from 'react'
import LabelValuePair from './label-value-pair'

interface PatientOverviewPersonalDetailsProps {
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

const PatientOverviewPersonalDetails: FC<PatientOverviewPersonalDetailsProps> = ({ details }) => {
  return (
    <div>
      <div className="font-poppins font-bold text-base leading-6 text-[#0F1011] mb-6">
        Personal Details
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-20 gap-y-6 text-sm">
        <LabelValuePair label="Full Name" value={details.fullName} />
        <LabelValuePair label="Contact Number" value={details.contactNumber} />
        <LabelValuePair label="Email" value={details.email} />
        <LabelValuePair label="Date of birth" value={details.dateOfBirth} />
        <LabelValuePair label="Emergency Contact Number" value={details.emergencyContact} />
        <LabelValuePair label="Family Contact Number" value={details.familyContact} />
        <LabelValuePair label="Blood Type" value={details.bloodType} />
        <LabelValuePair label="Marital Status" value={details.maritalStatus} />
        <LabelValuePair label="Occupation" value={details.occupation} />
        <LabelValuePair label="Preferred Language" value={details.preferredLanguage} />

        <div className="md:col-span-2">
          <LabelValuePair label="Address" value={details.address} />
        </div>
      </div>
    </div>
  )
}

export default PatientOverviewPersonalDetails