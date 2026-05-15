import { formatFee } from '@/utils/helper'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DoctorRevenueChartProps {
  monthlyPerformance?: Array<{
    month_label: string
    appointments: number
    revenue: number
  }>
  currency?: string
}

const DoctorRevenueChart: React.FC<DoctorRevenueChartProps> = ({ monthlyPerformance = [], currency = 'USD' }) => {
  // If no data → show empty chart or message
  if (monthlyPerformance.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center text-gray-500">
        No monthly performance data available
      </div>
    )
  }

  const chartData = monthlyPerformance.map(item => ({
    month: item.month_label,
    appointments: item.appointments,
    revenue: item.revenue
  }))

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart
        data={chartData}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
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
          label={{ value: 'Appointments', angle: -90, position: 'insideLeft', fontFamily: 'Poppins' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fill: '#64748B', fontFamily: 'Poppins', fontSize: 12 }}
          axisLine={{ stroke: '#E5E7EB' }}
          tickFormatter={(value) => `XCG ${value / 1000}k`}
          label={{ value: 'Revenue', angle: 90, position: 'insideRight', fontFamily: 'Poppins' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            fontFamily: 'Poppins'
          }}
          formatter={(value, name) => {
            const n = Number(value ?? 0)
            if (name === 'revenue') return [formatFee(n, currency), 'Revenue']
            return [n, 'Appointments']
          }}
        />
        <Legend
          wrapperStyle={{ fontFamily: 'Poppins', fontSize: '14px' }}
          formatter={(value) => value === 'appointments' ? 'Appointments' : 'Revenue'}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="appointments"
          stroke="#002FD4"
          strokeWidth={2}
          dot={{ fill: '#002FD4', r: 4 }}
          activeDot={{ r: 6 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="revenue"
          stroke="#0F1011"
          strokeWidth={2}
          dot={{ fill: '#0F1011', r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export default DoctorRevenueChart

