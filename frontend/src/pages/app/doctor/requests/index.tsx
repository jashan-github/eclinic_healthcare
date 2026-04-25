import RequestsLayout from '@/features/app/requests/components/requests-layout'
import { type FC, type ReactElement } from 'react'

const RequestsPage: FC = (): ReactElement => {
  return (
    <div className="h-full overflow-auto">
      <div className="flex bg-white flex-row gap-4 p-4 h-full overflow-y-scroll">
        <div className="w-12/12">
          <RequestsLayout />
        </div>
      </div>
    </div>
  )
}

export default RequestsPage
