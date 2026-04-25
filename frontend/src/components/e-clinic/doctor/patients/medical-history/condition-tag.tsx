// ConditionTag.tsx
import { type FC } from 'react'

interface ConditionTagProps {
    label: string
    isActive: boolean
    years?: string | null
}

const ConditionTag: FC<ConditionTagProps> = ({ label, isActive, years }) => {
    const bg = isActive ? 'bg-[#E3F8E6]' : 'bg-[#F4F6F9]'
    const textColor = isActive ? '#1F832D' : '#0F1011'

    return (
        <div className="flex items-center gap-2 py-1">
            {/* Y/N Badge */}
            <span
                className={`font-poppins font-bold text-[16px] leading-[18px] ${bg} px-2.5 py-1.5 rounded-full flex items-center justify-center min-w-[32px]`}
                style={{
                    color: textColor,
                }}
            >
                {isActive ? 'Y' : 'N'}
            </span>

            {/* Label Text */}
            <span className="font-poppins font-medium text-[14px] leading-[24px] text-[#0F1011]">
                {label}
            </span>

            {/* Duration Tag (only if active) */}
            {isActive && years && (
                <span className="px-3 py-1 bg-white text-[14px] font-poppins font-normal rounded-md border border-[#E4E5ED] text-[#0F1011] ml-1">
                    {years}
                </span>
            )}
        </div>
    )
}

export default ConditionTag