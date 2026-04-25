import { useState } from 'react'
import { useSearch } from '@tanstack/react-router'
import { Button, Stack, Text, Title, Loader } from '@mantine/core'
import { XIcon } from '@phosphor-icons/react'

interface PaymentProcessingSearch {
  payment_id?: string
  status?: string
}

export default function PaymentProcessingPage() {
  const search = useSearch({ from: '/app/_app-layout/(common)/payment/processing' }) as PaymentProcessingSearch
  const [isClosing, setIsClosing] = useState(false)

  const handleClose = () => {
    if (isClosing) return
    setIsClosing(true)
    
    // Notify parent window to refresh before closing
    if (window.opener && !window.opener.closed) {
      try {
        // Send message to parent to refresh
        window.opener.postMessage(
          { type: 'PAYMENT_PROCESSING', payment_id: search?.payment_id, status: search?.status },
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
          {/* Processing Icon */}
          <div className="flex items-center justify-center w-20 h-20 rounded-full bg-blue-100">
            <Loader size={48} color="#002FD4" />
          </div>

          {/* Title */}
          <Title order={2} className="font-poppins font-bold text-gray-900">
            Payment Processing
          </Title>

          {/* Message */}
          <Text size="md" className="text-gray-600 font-poppins">
            Your payment is being processed. Please wait...
          </Text>

          {/* Payment Details */}
          {search?.payment_id && (
            <div className="w-full bg-gray-50 rounded-lg p-4">
              <Text size="sm" className="text-gray-700 font-poppins">
                Payment ID: <span className="font-semibold">{search.payment_id}</span>
              </Text>
              {search?.status && (
                <Text size="sm" className="text-gray-700 font-poppins mt-1">
                  Status: <span className="font-semibold text-blue-600">{search.status}</span>
                </Text>
              )}
            </div>
          )}

          {/* Manual Close Button */}
          <Button
            onClick={handleClose}
            size="md"
            variant="outline"
            className="w-full border-[#002FD4] text-[#002FD4] hover:bg-[#002FD4] hover:text-white font-poppins font-semibold"
            leftSection={<XIcon size={20} />}
          >
            Close Window
          </Button>
        </Stack>
      </div>
    </div>
  )
}

