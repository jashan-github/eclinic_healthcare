import type { FC, ReactElement } from "react"
import RecentTable from "./recent-table"
import HeadSubhead from "./head-subhead"

interface ActivityItem {
  initials: string
  name: string
  action: string
  timeAgo: string
}

interface RecentActivityCardProps {
  activities: ActivityItem[]
}

const RecentActivityCard: FC<RecentActivityCardProps> = ({
  activities,
}): ReactElement => {
  return (
    <div className="bg-white h-[518px] rounded-2xl p-6 flex flex-col shadow-[6px_7px_20px_0px_#0000001A] border border-[#E2E8F0]">
      <div className="mb-10">
        <HeadSubhead head={"Recent Activity"} subhead={"Latest actions across the platform"} />
      </div>

      <RecentTable activities={activities} />
    </div>
  )
}

export default RecentActivityCard
