import type { FC } from "react";
import { useState } from "react";
import { WebinarItem } from "./webinar-item";
import { useDoctorWebinars } from "@/hooks/use-doctor-webinars";
import { format, isAfter, isBefore, parseISO, subMinutes } from "date-fns";
import AgoraWebinarRoom from "./agora-webinar-room";
import { useAuth } from "@/context/auth/auth-context-utils";

interface Props {
  searchTerm?: string;
  sortAsc?: boolean | null;
  consultType?: "online" | "offline" | null;
}

export const UpcomingWebinarContent: FC<Props> = ({
  searchTerm = "",
  sortAsc = null,
}) => {
  const { data, isLoading, error } = useDoctorWebinars();
  const upcomingWebinars = data?.upcomingWebinars || [];
  const { user } = useAuth();
  const [activeWebinar, setActiveWebinar] = useState<any | null>(null);
  const [joinRole, setJoinRole] = useState<"host" | "audience">("host");

  const handleStartWebinar = (webinar: any) => {
    setJoinRole("host");
    setActiveWebinar(webinar);
  };

  const handleJoinAsAudience = (webinar: any) => {
    setJoinRole("audience");
    setActiveWebinar(webinar);
  };

  const handleLeaveWebinar = () => {
    setActiveWebinar(null);
  };

  // If webinar is active, show Agora room
  if (activeWebinar) {
    return (
      <AgoraWebinarRoom
        webinarId={activeWebinar.id}
        isHost={joinRole === "host"}
        userRole="doctor"
        userName={user?.name || "Doctor"}
        onLeave={handleLeaveWebinar}
      />
    );
  }

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#002FD4] mx-auto"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        Failed to load upcoming webinars. Please try again.
      </div>
    );
  }

  let filtered = upcomingWebinars;

  if (searchTerm) {
    filtered = filtered.filter((w) =>
      w.title.toLowerCase().includes(searchTerm.toLowerCase()),
    );
  }

  if (sortAsc !== null) {
    filtered = [...filtered].sort((a, b) => {
      const dateA = parseISO(`${a.webinar_date}T${a.start_time}`);
      const dateB = parseISO(`${b.webinar_date}T${b.start_time}`);
      return sortAsc
        ? dateA.getTime() - dateB.getTime()
        : dateB.getTime() - dateA.getTime();
    });
  }

  if (filtered.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No upcoming webinars found
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {filtered.map((webinar) => {
        // Combine date and time for proper datetime formatting
        const now = new Date();
        const startDateTime = `${webinar.webinar_date}T${webinar.start_time}`;
        const endDateTime = `${webinar.webinar_date}T${webinar.end_time}`;

        // Calculate duration in minutes
        const startDate = parseISO(startDateTime);
        const endDate = parseISO(endDateTime);
        const durationMinutes = Math.round(
          (endDate.getTime() - startDate.getTime()) / (1000 * 60),
        );
        const joinWindowStart = subMinutes(startDateTime, 5);
        const canJoin =
          isAfter(now, joinWindowStart) && isBefore(now, endDateTime);

        return (
          <WebinarItem
            key={webinar.id}
            type="upcoming"
            title={webinar.title}
            description={webinar.description}
            image={webinar.host.profile_image}
            date={format(startDate, "MMM dd, yyyy")}
            time={`${format(startDate, "hh:mm a")} - ${format(endDate, "hh:mm a")}`}
            duration={`${durationMinutes} min`}
            registered={`${webinar.registered_count}/${webinar.participant_limit}`}
            webinarId={webinar.id}
            channelName={webinar.agora_channel_name || undefined}
            token={webinar.agora_token}
            onStartWebinar={() => handleStartWebinar(webinar)}
            onJoinWebinar={() => handleJoinAsAudience(webinar)}
            is_registered={webinar.is_registered}
            can_join={canJoin}
            hostId={webinar.host_id}
            isFree={webinar.pricing_type === "free"}
            price={webinar.price}
            isFull={webinar.registered_count >= webinar.participant_limit}
          />
        );
      })}
    </div>
  );
};
