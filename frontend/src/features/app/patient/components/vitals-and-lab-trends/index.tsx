import PatientHeader from '@/components/e-clinic/doctor/patients/medical-history/patient-header'
import { type FC, type ReactElement } from 'react'
import VitalsAndLabTrendsTable from './vitals-and-lab-trends-table'
import { useParams } from '@tanstack/react-router'

const VitalsAndLabTrendsWrapper: FC = (): ReactElement => {
  const { patientId } = useParams({ strict: false })
  return (
    <div className="h-screen bg-gray-50">
      <div className="h-[60px] bg-white border-b border-gray-200 flex items-center px-2">
        <PatientHeader title="Patient vital signs" />
      </div>
      <div className="h-[calc(100vh-60px)] overflow-hidden">
        <VitalsAndLabTrendsTable patientId={patientId}/>
      </div>
    </div>
  )
}

export default VitalsAndLabTrendsWrapper
