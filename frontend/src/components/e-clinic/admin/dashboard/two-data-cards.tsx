import OverviewGraph from '@/components/ui/overview-graph'
import RecentActivityCard from '@/components/ui/recent-activity-table'
import { useDashboardRecentActivity } from '@/hooks/use-dashboard'
import { Loader } from '@mantine/core'
import type { FC, ReactElement } from 'react'

const TwoCards: FC = (): ReactElement => {
  const { data, isLoading, isError } = useDashboardRecentActivity()

  const activities = (data ?? []).map((item) => ({
    initials: item.user_initials,
    name: item.user_name,
    action: item.action,
    timeAgo: item.time_ago,
  }))

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <OverviewGraph />

      {isLoading ? (
        <div className="bg-white h-[518px] rounded-2xl p-6 flex justify-center items-center shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
          <Loader size="sm" />
        </div>
      ) : isError ? (
        <div className="bg-white h-[518px] rounded-2xl p-6 flex justify-center items-center shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
          <span className="text-[#64748B]">Failed to load recent activity</span>
        </div>
      ) : (
        <RecentActivityCard activities={activities} />
      )}
    </div>
  )
}

export default TwoCards
