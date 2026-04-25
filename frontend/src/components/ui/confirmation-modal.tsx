import Modal from './modal'
import { WarningIcon } from '@phosphor-icons/react'

interface ConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmButtonColor?: 'danger' | 'primary'
  isLoading?: boolean
}

const ConfirmationModal = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmButtonColor = 'danger',
  isLoading = false
}: ConfirmationModalProps) => {
  const handleConfirm = () => {
    onConfirm()
  }

  const footer = (
    <>
      <button
        type="button"
        onClick={handleConfirm}
        disabled={isLoading}
        className={`px-6 py-2.5 font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors ${
          confirmButtonColor === 'danger'
            ? 'bg-red-600 hover:bg-red-700 text-white disabled:bg-red-400'
            : 'bg-[#002FD4] hover:bg-[#001FB8] text-white disabled:bg-blue-400'
        }`}
      >
        {isLoading ? 'Processing...' : confirmText}
      </button>
      <button
        type="button"
        onClick={onClose}
        disabled={isLoading}
        className="px-6 py-2.5 bg-white border border-[#E4E5ED] hover:bg-[#F4F6F9] text-[#0F1011] font-poppins font-semibold
          text-[14px] leading-[20px] rounded-md transition-colors disabled:opacity-50"
      >
        {cancelText}
      </button>
    </>
  )

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={footer}
      maxWidth="md"
    >
      <div className="flex flex-col items-center text-center">
        <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <WarningIcon size={32} weight="fill" color="#DC2626" />
        </div>
        <p className="font-poppins font-normal text-[16px] leading-[24px] text-[#0F1011]">
          {message}
        </p>
      </div>
    </Modal>
  )
}

export default ConfirmationModal

