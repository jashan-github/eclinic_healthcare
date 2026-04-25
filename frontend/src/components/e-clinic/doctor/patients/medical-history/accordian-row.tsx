// components/AccordionRow.tsx
import { type FC, type ReactElement, useState } from 'react'
import { CaretDownIcon } from '@phosphor-icons/react'

interface AccordionRowProps {
  title: string
  children?: React.ReactNode
  badge?: 'Y' | 'N'
  badgeColor?: 'green' | 'gray'
}

const AccordionRow: FC<AccordionRowProps> = ({ title, children, badge, badgeColor = 'gray' }): ReactElement => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="bg-white py-3 px-2">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2">
          {badge && (
            <span
              className={`font-poppins font-bold text-[16px] leading-[18px] px-2.5 py-1.5 rounded-full flex items-center justify-center min-w-[32px] ${
                badgeColor === 'green' 
                  ? 'bg-[#E3F8E6] text-[#1F832D]' 
                  : 'bg-[#F4F6F9] text-[#0F1011]'
              }`}
            >
              {badge}
            </span>
          )}
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
            {title}
          </p>
        </div>
        <CaretDownIcon
          weight="bold"
          className="w-4 h-4 text-[#64748B] transition-transform duration-200"
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        />
      </div>

      {isOpen && (
        <div className="mt-3 font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
          {children}
        </div>
      )}
    </div>
  )
}

export default AccordionRow