import { ArrowLeftIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'

interface PatientHeaderProps {
  title: string
}

const PatientHeader: FC<PatientHeaderProps> = ({ title }): ReactElement => {
  return (
    <div
      className="gap-xs flex items-center flex-nowrap cursor-pointer select-none"
      onClick={() => window.history.back()}
    >
      <div className="bg-[#F2F4F7] p-1 rounded-full">
        <ArrowLeftIcon
          size={18}
          weight="bold"
        />
      </div>

      <div className="font-poppins font-bold text-base leading-6 text-[#0F1011]">
        {title}
      </div>
    </div>
  )
}

export default PatientHeader
