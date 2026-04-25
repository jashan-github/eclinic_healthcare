// visits-details-wrapper.tsx
import { CalendarXIcon } from '@phosphor-icons/react'
import { type FC, type ReactElement } from 'react'
import VisitsDetails from './visits-details'

interface VisitsDetailsWrapperProps {
  pdfBlob?: Blob | null
  isPdfLoading: boolean
  pdfError?: Error | null
}

const VisitsDetailsWrapper: FC<VisitsDetailsWrapperProps> = ({
  pdfBlob,
  isPdfLoading,
  pdfError,
}): ReactElement => {
  const hasVisit = true // you can make this dynamic later: !!selectedVisitId

  if (!hasVisit) {
    return (
      <div className="w-full h-full border-l border-gray-200">
        <div className="w-full flex justify-center items-center h-full">
          <div className="flex flex-col items-center justify-center gap-xs">
            <CalendarXIcon color={'gray.2'} size={56} />
            <div className="text-gray-600 text-sm">
              No visit from this patient yet.
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <VisitsDetails 
      pdfBlob={pdfBlob}
      isPdfLoading={isPdfLoading}
      pdfError={pdfError}
    />
  )
}

export default VisitsDetailsWrapper