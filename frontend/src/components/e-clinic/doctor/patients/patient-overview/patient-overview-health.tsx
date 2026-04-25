// patient-overview-health.tsx
import { WarningIcon } from '@phosphor-icons/react'
import { type FC } from 'react'

interface PatientOverviewHealthProps {
  patient: {
    health_issues: string[]
  }
}

const PatientOverviewHealth: FC<PatientOverviewHealthProps> = ({ patient }) => {
  const healthIssues = patient?.health_issues ?? []

  return (
    <div className="gap-3 px-3 py-1.5 flex flex-col">
      <span className="inline-flex gap-1 font-poppins font-bold text-base leading-6 text-[#0F1011]">
        <WarningIcon color="#F59F0A" className="w-5 h-5" />
        Health Issue{healthIssues.length !== 1 ? 's' : ''}
      </span>

      {healthIssues.length > 0 ? (
        healthIssues.map((issue, index) => (
          <p
            key={index}
            className="font-poppins font-medium text-sm leading-5 text-[#545D69] ml-6"
          >
            • {issue}
          </p>
        ))
      ) : (
        <p className="font-poppins font-medium text-sm leading-5 text-[#545D69] ml-6">
          Not available
        </p>
      )}
    </div>
  )
}

export default PatientOverviewHealth