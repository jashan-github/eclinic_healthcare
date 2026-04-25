import { useEffect, useState, useCallback } from 'react'
import { useSearch } from '@tanstack/react-router'
import { Button, Stack, Text, Title } from '@mantine/core'
import { CheckCircleIcon, XIcon } from '@phosphor-icons/react'

interface PaymentSuccessSearch {
  payment_id?: string
  status?: string
}

export default function PaymentSuccessPage() {
  const search = useSearch({ from: '/app/_app-layout/(common)/payment/success' }) as PaymentSuccessSearch
  const [countdown, setCountdown] = useState(5)
  const [isClosing, setIsClosing] = useState(false)

  const handleClose = useCallback(() => {
    if (isClosing) return
    setIsClosing(true)
    
    // Notify parent window to refresh before closing
    if (window.opener && !window.opener.closed) {
      try {
        // Send message to parent to refresh
        window.opener.postMessage(
          { type: 'PAYMENT_SUCCESS', payment_id: search?.payment_id },
          window.location.origin
        )
        // Also trigger refresh directly
        window.opener.location.reload()
      } catch (error) {
        console.error('Failed to communicate with parent window:', error)
      }
    }
    
    // Close the popup after a short delay to ensure message is sent
    setTimeout(() => {
      window.close()
    }, 200)
  }, [isClosing, search?.payment_id])

  useEffect(() => {
    // Auto-close timer
    if (countdown > 0 && !isClosing) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1)
      }, 1000)
      return () => clearTimeout(timer)
    } else if (countdown === 0 && !isClosing) {
      handleClose()
    }
  }, [countdown, isClosing, handleClose])

  // Check if opened in popup
  const isPopup = window.opener !== null

  return (
    <div className={`${isPopup ? 'h-screen' : 'min-h-screen'} flex items-center justify-center bg-gray-50 p-4`}>
      <div className="bg-white rounded-lg shadow-lg p-6 md:p-8 max-w-md w-full text-center">
        <Stack gap="lg" align="center">
          {/* Success Icon */}
          <div className="flex items-center justify-center w-20 h-20 rounded-full bg-green-100">
            <CheckCircleIcon size={48} weight="fill" className="text-green-600" />
          </div>

          {/* Title */}
          <Title order={2} className="font-poppins font-bold text-gray-900">
            Payment Successful!
          </Title>

          {/* Message */}
          <Text size="md" className="text-gray-600 font-poppins">
            Your payment has been processed successfully.
          </Text>

          {/* Payment Details */}
          {search?.payment_id && (
            <div className="w-full bg-gray-50 rounded-lg p-4">
              <Text size="sm" className="text-gray-700 font-poppins">
                Payment ID: <span className="font-semibold">{search.payment_id}</span>
              </Text>
              {search?.status && (
                <Text size="sm" className="text-gray-700 font-poppins mt-1">
                  Status: <span className="font-semibold text-green-600">{search.status}</span>
                </Text>
              )}
            </div>
          )}

          {/* Auto-close countdown */}
          <Text size="sm" className="text-gray-500 font-poppins">
            This window will close automatically in {countdown} second{countdown !== 1 ? 's' : ''}
          </Text>

          {/* Manual Close Button */}
          <Button
            onClick={handleClose}
            size="md"
            className="w-full bg-[#002FD4] hover:bg-[#0020B0] font-poppins font-semibold"
            leftSection={<XIcon size={20} />}
          >
            Close Window
          </Button>
        </Stack>
      </div>
    </div>
  )
}

