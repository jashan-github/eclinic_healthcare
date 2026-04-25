import { type ReactNode } from 'react'

interface RadioButtonProps {
  value: string
  checked: boolean
  onChange: (value: string) => void
  name: string
  icon?: ReactNode
  title: string
  description?: string
  className?: string
}

const RadioButton = ({
  value,
  checked,
  onChange,
  name,
  icon,
  title,
  description,
  className = ''
}: RadioButtonProps) => {
  return (
    <label
      className={`flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-colors hover:bg-[#F4F6F9] ${className}`}
      style={{ borderColor: checked ? '#002FD4' : '#E4E5ED' }}
    >
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1"
      />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          {icon && icon}
          <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
            {title}
          </span>
        </div>
        {description && (
          <p className="font-poppins font-normal text-[12px] leading-[16px] text-[#64748B]">
            {description}
          </p>
        )}
      </div>
    </label>
  )
}

export default RadioButton

