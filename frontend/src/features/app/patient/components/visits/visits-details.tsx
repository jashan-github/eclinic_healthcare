// visits-details.tsx
import { Loader } from '@mantine/core'
// import { PrinterIcon } from '@phosphor-icons/react'
import { useEffect, useState, type FC, type ReactElement } from 'react'

interface VisitsDetailsProps {
  pdfBlob?: Blob | null
  isPdfLoading: boolean
  pdfError?: Error | null
}

const VisitsDetails: FC<VisitsDetailsProps> = ({
  pdfBlob,
  isPdfLoading,
  pdfError,
}): ReactElement => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  // Create object URL when blob arrives
  useEffect(() => {
    if (pdfBlob) {
      const url = URL.createObjectURL(pdfBlob)
      setPdfUrl(url)

      // Cleanup on unmount or new blob
      return () => {
        URL.revokeObjectURL(url)
      }
    }
  }, [pdfBlob])

  return (
    <div className="flex flex-col w-full h-full border-l border-gray-200">
      {/* Top Bar */}
      <div className="flex items-center justify-start h-10 w-full px-4 border-b border-gray-200">
        <div className="font-bold text-primary text-sm">Prescription</div>
      </div>

      {/* Content */}
      <div className="grow w-full flex flex-col">
        {isPdfLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader size="lg" />
            <span className="ml-3 text-gray-600">Loading prescription...</span>
          </div>
        ) : pdfError ? (
          <div className="flex-1 flex items-center justify-center text-red-600">
            Failed to load prescription: {pdfError.message}
          </div>
        ) : pdfUrl ? (
          <iframe
            src={pdfUrl}
            className="w-full h-full border-none"
            title="Prescription PDF"
          />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a visit to view prescription
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      {/* <div className="flex h-12 w-full border-t border-gray-200 justify-end items-center p-4">
        <Button
          leftSection={<PrinterIcon size={20} weight={'fill'} />}
          disabled={!pdfUrl}
          onClick={() => {
            if (pdfUrl) {
              const link = document.createElement('a')
              link.href = pdfUrl
              link.download = 'prescription.pdf'
              link.click()
            }
          }}
        >
          Print / Download
        </Button>
      </div> */}
    </div>
  )
}

export default VisitsDetails