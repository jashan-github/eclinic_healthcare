// past-webinar.tsx
import type { FC } from "react"
import { WebinarItem } from "./webinar-item"
import { useDoctorWebinars } from "@/hooks/use-doctor-webinars"

interface Props {
  searchTerm?: string
  sortAsc?: boolean | null
  consultType?: 'online' | 'offline' | null
}

export const PastWebinarContent: FC<Props> = ({ searchTerm = '', sortAsc = null }) => {
  const { data, isLoading, error } = useDoctorWebinars()

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#002FD4]"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Failed to load webinars. Please try again.
      </div>
    )
  }

  let filtered = data?.pastWebinars || []

  // Apply search filter
  if (searchTerm) {
    filtered = filtered.filter(w => 
      w.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      w.description?.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }

  // Apply sorting
  if (sortAsc !== null) {
    filtered = [...filtered].sort((a, b) => {
      const dateA = new Date(`${a.webinar_date}T${a.end_time}`)
      const dateB = new Date(`${b.webinar_date}T${b.end_time}`)
      return sortAsc ? dateA.getTime() - dateB.getTime() : dateB.getTime() - dateA.getTime()
    })
  }

  if (filtered.length === 0) {
    return <div className="text-center py-8 text-gray-500">No past webinars found</div>
  }

  return (
    <div className="space-y-4">
      {filtered.map(webinar => {
        // Format date for display
        const displayDate = webinar.webinar_date
        
        // Format time for display (convert 24h to 12h format)
        const [hours, minutes] = webinar.end_time.split(':')
        const hour = parseInt(hours)
        const ampm = hour >= 12 ? 'PM' : 'AM'
        const hour12 = hour % 12 || 12
        const displayTime = `${String(hour12).padStart(2, '0')}:${minutes} ${ampm}`

        // Calculate duration in minutes
        const [startHours, startMinutes] = webinar.start_time.split(':')
        const startTotalMinutes = parseInt(startHours) * 60 + parseInt(startMinutes)
        const [endHours, endMinutes] = webinar.end_time.split(':')
        const endTotalMinutes = parseInt(endHours) * 60 + parseInt(endMinutes)
        const durationMinutes = endTotalMinutes - startTotalMinutes
        const duration = `${durationMinutes} min`

        // Format registered/attended count
        const registered = `${webinar.attended_count}/${webinar.participant_limit}`

        return (
          <WebinarItem
            key={webinar.id}
            type="completed"
            title={webinar.title}
            image={webinar.host.profile_image}
            description={webinar.description}
            date={displayDate}
            time={displayTime}
            duration={duration}
            registered={registered}
          />
        )
      })}
    </div>
  )
}