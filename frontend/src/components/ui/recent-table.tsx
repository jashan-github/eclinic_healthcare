import type { FC, ReactElement } from "react"

interface Activity {
  initials: string
  name: string
  action: string
  timeAgo: string
}

interface RecentTableProps {
  activities: Activity[]
}

const RecentTable: FC<RecentTableProps> = ({ activities }): ReactElement => {
  return (
    <div className="flex flex-col gap-10 overflow-auto">
      {activities.map((activity, index) => (
        <div key={index} className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#E9F0FF] text-[#002FD4] font-semibold text-sm">
              {activity.initials}
            </div>
            <div className="flex flex-col">
              <span className="font-poppins font-semibold text-[14px] leading-[20px]">
                {activity.name}
              </span>
              <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#627084]">
                {activity.action}
              </span>
            </div>
          </div>
          <div className=" flex h-full items-end font-poppins font-normal text-[12px] leading-[16px] text-[#627084]">
            {activity.timeAgo}
          </div>
        </div>
      ))}
    </div>
  )
}

export default RecentTable
