import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useAdminWebinarsGraph } from '@/hooks/use-analytics'
import { Loader } from '@mantine/core'

const WebinarChart = () => {
  const { data, isLoading, isError } = useAdminWebinarsGraph()

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
        Failed to load webinar data
      </div>
    )
  }

  const chartData = data.map((point) => ({
    month: point.month_label,
    total_webinars: point.total_webinars,
    amount_collected: point.amount_collected,
  }))

  return (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart
        data={chartData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <defs>
          <linearGradient id="gradientWebinars" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#002FD4" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#002FD4" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradientAmountWebinar" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10B981" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#10B981" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis
          dataKey="month"
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
        />
        <YAxis
          yAxisId="left"
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
          tickFormatter={(value) => value >= 1000 ? `${value / 1000}k` : `${value}`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            fontFamily: 'Poppins'
          }}
          formatter={(value: number, name: string) => {
            if (name === 'amount_collected') return [`$${value.toLocaleString()}`, '']
            return [value, '']
          }}
        />
        <Legend
          wrapperStyle={{
            fontFamily: 'Poppins',
            fontSize: '14px'
          }}
          formatter={(value) => {
            if (value === 'total_webinars') return 'Total Webinars'
            if (value === 'amount_collected') return 'Amount Collected'
            return value
          }}
        />
        <Area
          yAxisId="left"
          type="monotone"
          dataKey="total_webinars"
          stroke="#002FD4"
          strokeWidth={2}
          fill="url(#gradientWebinars)"
          dot={{ fill: '#002FD4', r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Area
          yAxisId="right"
          type="monotone"
          dataKey="amount_collected"
          stroke="#10B981"
          strokeWidth={2}
          fill="url(#gradientAmountWebinar)"
          dot={{ fill: '#10B981', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default WebinarChart
