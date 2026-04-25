import { type ReactNode, type ButtonHTMLAttributes } from 'react'

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  className?: string
  icon?: ReactNode
  iconPosition?: 'left' | 'right'
}

const Button = ({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  icon,
  iconPosition = 'left',
  ...props
}: ButtonProps) => {
  const baseClasses = 'font-poppins font-semibold rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-[#002FD4] disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variantClasses = {
    primary: 'bg-[#002FD4] hover:bg-[#001FB8] text-white',
    secondary: 'bg-white border border-[#E4E5ED] hover:bg-[#F4F6F9] text-[#0F1011]',
    ghost: 'bg-transparent hover:bg-[#F4F6F9] text-[#0F1011]',
    icon: 'p-1.5 hover:bg-[#F4F6F9] rounded-md text-gray-600'
  }
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-[12px] leading-[18px]',
    md: 'px-6 py-2.5 text-[14px] leading-[20px]',
    lg: 'px-8 py-3 text-[16px] leading-[24px]'
  }
  
  const iconSizeClasses = {
    sm: 'p-1',
    md: 'p-1.5',
    lg: 'p-2'
  }
  
  if (variant === 'icon') {
    return (
      <button
        {...props}
        className={`${baseClasses} ${iconSizeClasses[size]} ${className}`}
      >
        {children}
      </button>
    )
  }
  
  const finalClasses = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`
  
  return (
    <button
      {...props}
      className={finalClasses}
    >
      <span className="flex items-center gap-2">
        {icon && iconPosition === 'left' && <span>{icon}</span>}
        {children}
        {icon && iconPosition === 'right' && <span>{icon}</span>}
      </span>
    </button>
  )
}

export default Button

