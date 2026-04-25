import { type FC, type ReactElement } from 'react'
import { CalendarBlankIcon, CameraIcon, CurrencyDollarIcon, UsersIcon, } from '@phosphor-icons/react'
import { SingleCard } from './single-card'
import { useAdminAnalyticsStats } from '@/hooks/use-analytics'
import { Loader } from '@mantine/core'

const FourAnalyticsCards: FC = (): ReactElement => {
  const { data, isLoading, isError } = useAdminAnalyticsStats()

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <Loader size="sm" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="text-center text-[#64748B] py-8">
        Failed to load analytics stats
      </div>
    )
  }

  const cards = [
    { id: 1, title: 'Total Webinars', value: data.total_webinars, Icon: CameraIcon },
    { id: 2, title: 'Total Appointments', value: data.total_appointments, Icon: CalendarBlankIcon },
    { id: 3, title: 'Revenue', value: data.revenue, Icon: CurrencyDollarIcon },
    { id: 4, title: 'Active Patients', value: data.active_patients, Icon: UsersIcon }
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((c) => (
        <SingleCard
          key={c.id}
          title={c.title}
          value={c.value}
          Icon={c.Icon}
          currency={data.currency}
        />
      ))}
    </div>
  )
}

export default FourAnalyticsCards
