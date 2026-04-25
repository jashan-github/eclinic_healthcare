// components/LabelValuePair.tsx
import { type FC, type ReactNode } from 'react'

interface LabelValuePairProps {
  label: string
  value: ReactNode
}

const LabelValuePair: FC<LabelValuePairProps> = ({ label, value }) => {
  return (
    <div className='flex flex-col gap-2'>
      <p className="font-poppins font-medium text-sm leading-5 text-[#545D69]">{label}</p>
      <p className="font-poppins font-medium text-sm leading-5 text-[#A5ABB3D9]">{value}</p>
    </div>
  )
}

export default LabelValuePair