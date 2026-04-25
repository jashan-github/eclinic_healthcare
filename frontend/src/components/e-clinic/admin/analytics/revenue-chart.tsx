import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useAdminRevenueGraph } from '@/hooks/use-analytics'
import { Loader } from '@mantine/core'

const RevenueChart = () => {
  const { data, isLoading, isError } = useAdminRevenueGraph()

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-[400px]">
        <Loader size="sm" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="flex justify-center items-center h-[400px] text-[#64748B]">
        Failed to load revenue data
      </div>
    )
  }

  const chartData = data.map((point) => ({
    month: point.month_label,
    primary_revenue: point.primary_revenue,
    secondary_revenue: point.secondary_revenue,
  }))

  const maxRevenue = Math.max(
    ...data.map((p) => Math.max(p.primary_revenue, p.secondary_revenue)),
    1
  )
  const yMax = Math.ceil(maxRevenue / 1000) * 1000

  return (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart
        data={chartData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <defs>
          <linearGradient id="gradientPrimary" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0F1011" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#0F1011" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradientSecondary" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#002FD4" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#002FD4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis
          dataKey="month"
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
        />
        <YAxis
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
          tickFormatter={(value) => value >= 1000 ? `${value / 1000}k` : `${value}`}
          domain={[0, yMax || 'auto']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            fontFamily: 'Poppins'
          }}
          formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
        />
        <Legend
          wrapperStyle={{
            fontFamily: 'Poppins',
            fontSize: '14px'
          }}
          formatter={(value) => {
            if (value === 'primary_revenue') return 'Primary Revenue'
            if (value === 'secondary_revenue') return 'Secondary Revenue'
            return value
          }}
        />
        <Area
          type="monotone"
          dataKey="primary_revenue"
          stroke="#0F1011"
          strokeWidth={2}
          fill="url(#gradientPrimary)"
          dot={{ fill: '#0F1011', r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Area
          type="monotone"
          dataKey="secondary_revenue"
          stroke="#002FD4"
          strokeWidth={2}
          fill="url(#gradientSecondary)"
          dot={{ fill: '#002FD4', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default RevenueChart
