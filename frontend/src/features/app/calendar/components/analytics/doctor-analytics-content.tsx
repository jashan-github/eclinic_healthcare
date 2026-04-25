import { type FC, type ReactElement } from 'react'
import AnalyticsCards from './analytics-cards'
import AnalyticsTabs from './analytics-tabs'
import DoctorRevenueChart from './doctor-revenue-chart'
import { useAnalyticsReport } from '@/hooks/use-analytics'

const DoctorAnalyticsContent: FC = (): ReactElement => {
  const { data: report, isLoading, error } = useAnalyticsReport()
  if (isLoading) return <div>Loading report...</div>
  if (error) return <div>Error: {error.message}</div>
  const { summary, monthly_performance, top_medical_metrics, payment_breakdown } = report ?? {}

  return (
    <div className="bg-white flex flex-col gap-6 p-6">
      <AnalyticsCards summary={summary} />

      {/* Chart Section */}
      <div className="bg-white rounded-2xl border border-[#DAE0E7] shadow-[6px_7px_20px_0px_#0000001A] p-8 border border-[#E2E8F0]">
        <div className="mb-6">
          <h2 className="font-poppins font-semibold text-[18px] leading-5 tracking-normal align-middle text-[#0F1011]">
            Monthly Performance Analysis
          </h2>
          <p className="font-poppins font-normal text-sm leading-5 tracking-normal align-middle text-[#627084] mt-1">
            Monthly appointments and revenue trends
          </p>
        </div>

        {/* Chart Area */}
        <div className="h-[400px]">
          <DoctorRevenueChart
            monthlyPerformance={monthly_performance}
            currency={summary?.currency}
          />
        </div>
      </div>

      <AnalyticsTabs
        topMedical={top_medical_metrics}
        payment={payment_breakdown}
      />
    </div>
  )
}

export default DoctorAnalyticsContent
