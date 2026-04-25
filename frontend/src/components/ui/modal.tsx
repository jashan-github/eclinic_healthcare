import { XIcon } from '@phosphor-icons/react'
import { type ReactNode } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  footer?: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  showCloseButton?: boolean
}

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  maxWidth = '2xl',
  showCloseButton = true
}: ModalProps) => {
  if (!isOpen) return null

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl'
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div className={`bg-white rounded-lg ${maxWidthClasses[maxWidth]} w-full max-h-[90vh] overflow-y-auto shadow-xl`}>
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-[#E4E5ED]">
            {title && (
              <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011]">
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                type="button"
                onClick={onClose}
                className="p-2 hover:bg-[#F4F6F9] rounded-md transition-colors"
                aria-label="Close modal"
              >
                <XIcon size={20} weight="bold" color="#64748B" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-between gap-4 p-6 border-t border-[#E4E5ED] bg-[#F4F6F9] bg-opacity-50">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

export default Modal
