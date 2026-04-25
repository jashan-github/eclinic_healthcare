import { type FC } from "react";
import {
  VideoCamera,
  Clock,
  Calendar,
  GearSixIcon,
  UserIcon,
  ShareIcon,
} from "@phosphor-icons/react";
import { useAuth } from "@/context/auth/auth-context-utils";
import { useRegisterForWebinar } from "@/hooks/use-webinar-registeration";
import { toast } from "react-toastify";

interface WebinarItemProps {
  type: "live" | "upcoming" | "completed";
  title: string;
  description: string;
  date?: string;
  time?: string;
  duration?: string;
  registered?: string;
  attendees?: string;
  isFree?: boolean;
  price?: number;
  image?: string | null;
  webinarId?: string;
  channelName?: string;
  token?: string | null;
  onJoinWebinar?: () => void;
  onStartWebinar?: () => void;
  is_registered?: boolean;
  can_join?: boolean;
  hostId?: string;
  isFull?: boolean;
}

export const WebinarItem: FC<WebinarItemProps> = ({
  type,
  title,
  description,
  date,
  time,
  image,
  duration,
  registered,
  onJoinWebinar,
  onStartWebinar,
  is_registered,
  can_join,
  hostId,
  webinarId,
  isFull,
}) => {
  const isLive = type === "live";

  const { mutate: registerWebinar } = useRegisterForWebinar();

  const handleRegisteration = () => {
    if (!webinarId) {
      toast.error("Webinar ID not available");
      return;
    }

    registerWebinar(
      { webinar_id: webinarId },
      {
        onSuccess: (response) => {
          // ✅ PAID webinar → backend sends payment_url
          const paymentUrl = response?.data?.payment?.payment_url;

          if (paymentUrl) {
            const popup = window.open(
              paymentUrl,
              "Payment",
              "width=800,height=600,scrollbars=yes,resizable=yes",
            );

            if (!popup) {
              toast.error("Please allow popups to proceed with payment");
            }

            return;
          }

          // ✅ FREE webinar → registration done
          toast.success("Registered successfully");
        },
        onError: () => {
          // Toast already handled in hook
        },
      },
    );
  };

  const handleJoinStream = () => {
    if (onJoinWebinar) {
      onJoinWebinar();
    }
  };

  const handleStart = () => {
    if (onStartWebinar) {
      onStartWebinar();
    }
  };

  const { user } = useAuth();

  const isHost = hostId === user?.id;

  const renderPrimaryAction = () => {
    // HOST FLOW
    if (isHost) {
      return (
        <button
          disabled={!can_join}
          onClick={can_join ? handleStart : undefined}
          className={`px-5 py-2.5 rounded-md font-poppins text-sm font-medium
          ${
            can_join
              ? "bg-[#002FD4] text-white hover:bg-[#002bb8]"
              : "bg-[#002FD4] text-white opacity-50 cursor-not-allowed"
          }`}
        >
          Go Live
        </button>
      );
    }

    // NON-HOST FLOW
    if (!can_join && is_registered) {
      return (
        <button
          disabled={!can_join}
          onClick={can_join ? handleJoinStream : undefined}
          className={`px-5 py-2.5 rounded-md font-poppins text-sm font-medium
          ${
            can_join
              ? "bg-[#002FD4] text-white hover:bg-[#002bb8]"
              : "bg-[#002FD4] text-white opacity-50 cursor-not-allowed"
          }`}
        >
          Join
        </button>
      );
    }

    if (isFull) {
      return (
        <button
          disabled
          className="px-5 py-2.5 bg-gray-300 text-gray-600 font-poppins text-sm font-medium rounded-md cursor-not-allowed"
        >
          Seats Full
        </button>
      );
    }

    return (
      <button
        onClick={handleRegisteration}
        className="px-5 py-2.5 bg-[#002FD4] text-white font-poppins text-sm font-medium rounded-md hover:bg-[#002bb8]"
      >
        Register
      </button>
    );
  };

  return (
    <div
      className={`bg-white rounded-md border border-gray-200 p-5 flex items-start gap-5 transition-shadow`}
    >
      <div className="flex-shrink-0">
        <div
          className={`w-12 h-12 rounded-full bg-[#E8EEFD] flex items-center justify-center`}
        >
          {image ? (
            <img
              src={image}
              alt={"Host"}
              className="w-full h-full object-cover rounded-full"
              onError={(e) => {
                e.currentTarget.style.display = "none";
                e.currentTarget.parentElement!.innerHTML = `<div class="w-full h-full flex items-center justify-center"><span class="text-white font-bold text-2xl">}</span></div>`;
              }}
            />
          ) : (
            <VideoCamera size={28} className="text-[#002FD4]" />
          )}
        </div>
      </div>

      <div className="flex-1 space-y-1">
        <div className="font-poppins font-semibold text-base leading-6 text-[#0F1011]">
          {title}
        </div>
        <div className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
          {description}
        </div>

        {isLive ? (
          <div className="flex items-center gap-4 text-sm text-[#64748B]">
            <span className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
              Started: 10:00 AM
            </span>
            <span className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
              01:15:30
            </span>
            <span className="font-poppins font-normal text-sm leading-5 text-[#64748B]">
              145,200 attendees
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-6 mt-3 text-sm text-[#64748B]">
            <span className="flex items-center gap-1.5">
              <Calendar size={16} weight="regular" />
              {date}
            </span>
            <span className="flex items-center gap-1.5">
              <Clock size={16} weight="regular" />
              {time} ({duration})
            </span>
            <span className="flex items-center gap-1.5">
              <UserIcon size={16} weight="regular" />
              {registered}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {isLive ? (
          <>
            <button className="text-[#64748B] hover:text-[#0F1011] transition-colors border-1 border-[#E2E8F0] px-3 py-2 rounded-md">
              <GearSixIcon size={20} color="#0F1011" />
            </button>
            <button
              onClick={handleJoinStream}
              className="px-5 py-2.5 bg-[#002FD4] text-white font-poppins text-sm font-medium rounded-md hover:bg-[#002bb8] transition-colors flex items-center gap-2"
            >
              <span className="font-poppins font-semibold text-sm leading-5 text-center">
                Join Stream
              </span>
            </button>
          </>
        ) : (
          <>
            {/* <button className="gap-2 text-[#0F1011] inline-flex transition-colors border-1 border-[#E2E8F0] px-3 py-2 rounded-md">
                            <GearSixIcon size={20} color='#0F1011' />
                            <span className="font-poppins font-semibold text-sm leading-5 text-center align-middle text-[#0F1011]">
                                Settings
                            </span>
                        </button> */}
            <div className="flex items-center gap-3">
              <button className="gap-2 text-[#0F1011] inline-flex transition-colors border border-[#E2E8F0] px-3 py-2 rounded-md">
                <ShareIcon size={20} color="#0F1011" />
                <span className="font-poppins font-semibold text-sm leading-5">
                  Share
                </span>
              </button>

              {renderPrimaryAction()}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
