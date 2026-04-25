import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import VisitsWrapper from '@/features/app/patient/components/visits'
import { type FC, type ReactElement } from 'react'

const PatientVisitsPage: FC = (): ReactElement => {
  return (
    <div className="h-screen flex flex-col gap-4">
      {/* Header */}
      <div className="h-[60px] bg-white px-2 w-full">
        <div className="h-full w-full flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="font-medium pl-2">
              <PatientHeader title="Past Visits" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <VisitsWrapper />
    </div>
  )
}

export default PatientVisitsPage
