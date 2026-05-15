import type { FC, ReactElement } from "react"
import HeadSubhead from "./head-subhead"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts'
import { useDashboardRevenueGraph } from '@/hooks/use-dashboard'
import { Loader } from '@mantine/core'

const OverviewGraph: FC = (): ReactElement => {
  const { data, isLoading, isError } = useDashboardRevenueGraph(6)

  if (isLoading) {
    return (
      <div className="bg-white h-[518px] rounded-2xl p-6 flex flex-col justify-center items-center shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
        <Loader size="sm" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="bg-white h-[518px] rounded-2xl p-6 flex flex-col justify-center items-center shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
        <span className="text-[#64748B]">Failed to load revenue data</span>
      </div>
    )
  }

  const chartData = data.map((point) => ({
    month: point.month_label,
    revenue: point.revenue,
  }))

  const maxRevenue = Math.max(...data.map((p) => p.revenue), 1)
  const yMax = Math.ceil(maxRevenue / 1000) * 1000

  return (
    <div className="bg-white h-[518px] rounded-2xl p-6 flex flex-col shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
      <HeadSubhead head={"Revenue Overview"} subhead={"Monthly revenue for last 6 months"} />
      <div className="flex-1 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="gradientDashboardRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#002FD4" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#002FD4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#E5E7EB"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12, fontFamily: 'Poppins' }}
              tickMargin={10}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#64748B', fontSize: 12, fontFamily: 'Poppins' }}
              tickMargin={10}
              tickFormatter={(value) => value >= 1000 ? `$${value / 1000}k` : `$${value}`}
              domain={[0, yMax || 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                padding: '8px 12px',
                fontFamily: 'Poppins',
                fontSize: '12px'
              }}
              formatter={(value) => [`$${Number(value ?? 0).toLocaleString()}`, 'Revenue']}
              labelStyle={{ fontFamily: 'Poppins', fontWeight: 600 }}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#002FD4"
              strokeWidth={3}
              fill="url(#gradientDashboardRevenue)"
              dot={{ fill: '#002FD4', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default OverviewGraph
