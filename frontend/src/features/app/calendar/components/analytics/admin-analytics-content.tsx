import { type FC, type ReactElement } from 'react'
import HeadSubhead from '@/components/ui/head-subhead'
import FourAnalyticsCards from '@/components/e-clinic/admin/analytics/four-analytics-cards'
import AnalyticsDashboard from '@/components/e-clinic/admin/analytics/analytics-tabs'

const AdminAnalyticsContent: FC = (): ReactElement => {
  return (
    <>
      <div className="h-full bg-[#F4F6F9]">
        <div className="p-4 h-full">
          <div className="flex justify-between items-center p-6">
            <HeadSubhead
              head={'Advanced Analytics'}
              subhead={'Comprehensive insights into revenue, appointments, and webinars'}
            />
          </div>
          <div className='p-4'>
            <FourAnalyticsCards />
          </div>
          <div className='p-4'>
            <AnalyticsDashboard />
          </div>
        </div>
      </div>
    </>
  )
}

export default AdminAnalyticsContent
