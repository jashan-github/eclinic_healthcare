import type { FC } from "react"
import { WebinarItem } from "./webinar-item"

interface LiveWebinar {
  id: string
  title: string
  description: string
  attendees: string
}

interface LiveWebinarContentProps {
  webinars?: LiveWebinar[]
}

export const LiveWebinarContent: FC<LiveWebinarContentProps> = ({ 
  webinars 
}) => {
  const liveWebinars: LiveWebinar[] = webinars || [
    {
      id: "1",
      title: "Heart Health Awareness",
      description: "Understanding cardiovascular disease prevention",
      attendees: "145,200",
    }
  ]

  if (liveWebinars.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 font-medium">
        No live webinars at the moment
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {liveWebinars.map((webinar) => (
        <WebinarItem
          key={webinar.id}
          type="live"
          title={webinar.title}
          description={webinar.description}
          attendees={webinar.attendees}
        />
      ))}
    </div>
  )
}
