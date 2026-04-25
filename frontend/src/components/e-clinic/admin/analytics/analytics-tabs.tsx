import { useState } from 'react'
import AnalyticsDashboardTabs from './analytics-dashboard-tabs'
import RevenueChart from './revenue-chart'
import AppointmentsChart from './appointments-chart'
import WebinarChart from './webinar-chart'

export default function AnalyticsDashboard() {
  const [activeTab, setActiveTab] = useState<'revenue' | 'appointments' | 'webinar'>('revenue')

  return (
    <div>
      {/* Tabs */}
      <div className="mb-8">
        <AnalyticsDashboardTabs activeTab={activeTab} onTabChange={setActiveTab} />
      </div>

      {/* Content Area */}
      <div className="bg-white rounded-2xl border border-[#DAE0E7] shadow-[6px_7px_20px_0px_#0000001A] p-8 border border-[#E2E8F0]">
        <div className="mb-6">
          <h2 className="font-poppins font-semibold text-[18px] leading-5 tracking-normal align-middle text-[#0F1011]">
            {activeTab === 'revenue' && 'Revenue Analysis'}
            {activeTab === 'appointments' && 'Appointment Volume'}
            {activeTab === 'webinar' && 'Webinar Performance'}
          </h2>
          <p className="font-poppins font-normal text-sm leading-5 tracking-normal align-middle text-[#627084] mt-1">
            {activeTab === 'revenue' && 'Monthly revenue analysis'}
            {activeTab === 'appointments' && 'Monthly appointment trends'}
            {activeTab === 'webinar' && 'Webinar attendance and performance'}
          </p>
        </div>

        {/* Chart Area */}
        <div className="h-[400px]">
          {activeTab === 'revenue' && <RevenueChart />}
          {activeTab === 'appointments' && <AppointmentsChart />}
          {activeTab === 'webinar' && <WebinarChart />}
        </div>
      </div>
    </div>
  )
}
