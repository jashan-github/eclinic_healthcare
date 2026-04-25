import AnalyticsCards from '@/features/app/calendar/components/analytics/analytics-cards'
import AnalyticsTabs from '@/features/app/calendar/components/analytics/analytics-tabs'
import { type FC, type ReactElement } from 'react'

const AnalyticsPage: FC = (): ReactElement => {
  return (
    <div className="h-screen overflow-auto bg-white">
      <div className="bg-white flex flex-col gap-6 p-6">
        <AnalyticsCards />
        <AnalyticsTabs />
      </div>
    </div>
  )
}

export default AnalyticsPage
