import { useState } from 'react'
import { useSearch } from '@tanstack/react-router'
import { Button, Stack, Text, Title } from '@mantine/core'
import { XCircleIcon } from '@phosphor-icons/react'

interface PaymentFailureSearch {
  payment_id?: string
  reason?: string
}

export default function PaymentFailurePage() {
  const search = useSearch({ from: '/app/_app-layout/(common)/payment/failure' }) as PaymentFailureSearch
  const [isClosing, setIsClosing] = useState(false)

  const handleClose = () => {
    if (isClosing) return
    setIsClosing(true)
    
    // Notify parent window to refresh before closing
    if (window.opener && !window.opener.closed) {
      try {
        // Send message to parent to refresh
        window.opener.postMessage(
          { type: 'PAYMENT_FAILURE', payment_id: search?.payment_id, reason: search?.reason },
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
  }

  // Check if opened in popup
  const isPopup = window.opener !== null

  return (
    <div className={`${isPopup ? 'h-screen' : 'min-h-screen'} flex items-center justify-center bg-gray-50 p-4`}>
      <div className="bg-white rounded-lg shadow-lg p-6 md:p-8 max-w-md w-full text-center">
        <Stack gap="lg" align="center">
          {/* Failure Icon */}
          <div className="flex items-center justify-center w-20 h-20 rounded-full bg-red-100">
            <XCircleIcon size={48} weight="fill" className="text-red-600" />
          </div>

          {/* Title */}
          <Title order={2} className="font-poppins font-bold text-gray-900">
            Payment Failed
          </Title>

          {/* Message */}
          <Text size="md" className="text-gray-600 font-poppins">
            {search?.reason 
              ? `Payment failed: ${search.reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`
              : 'Your payment could not be processed. Please try again.'}
          </Text>

          {/* Payment Details */}
          {search?.payment_id && (
            <div className="w-full bg-gray-50 rounded-lg p-4">
              <Text size="sm" className="text-gray-700 font-poppins">
                Payment ID: <span className="font-semibold">{search.payment_id}</span>
              </Text>
            </div>
          )}

          {/* Manual Close Button */}
          <Button
            onClick={handleClose}
            size="md"
            className="w-full bg-[#002FD4] hover:bg-[#0020B0] font-poppins font-semibold"
            leftSection={<XCircleIcon size={20} />}
          >
            Close Window
          </Button>
        </Stack>
      </div>
    </div>
  )
}

