import { formatFee } from "@/utils/helper";
import { CalendarIcon, ClockIcon, UsersIcon } from "@phosphor-icons/react";
import { isAfter, subMinutes } from "date-fns";

interface Webinar {
  id: string;
  doctorName: string;
  doctorSpecialty: string;
  doctorImage: string;
  title: string;
  date: string;
  time: string;
  duration: string;
  capacity: {
    filled: number;
    total: number;
  };
  price: number | null; // null means free
  pricingType: "free" | "paid";
  can_join: boolean;
  startDateTime: Date;
  doctorExperience?: string;
  doctorDescription?: string;
  webinarDescription?: string;
  currency?: string;
  host_id: string;
  is_registered: boolean;
}

interface WebinarCardProps {
  webinar: Webinar;
  onRegister: (webinar: Webinar) => void;
  onJoin?: (webinar: Webinar) => void;
}

const WebinarCard = ({ webinar, onRegister, onJoin }: WebinarCardProps) => {
  const now = new Date();
  const joinWindowStart = subMinutes(webinar.startDateTime, 5);
  const canJoinNow = isAfter(now, joinWindowStart);
  const isFull = webinar.capacity.filled >= webinar.capacity.total;
  const isFree = webinar.pricingType === "free";
  const alreadyRegistered = webinar.is_registered;
  // let buttonText = "Register";
  let buttonText = "";
  let buttonDisabled = false;
  let buttonStyle = "";
  const defaultButtonStyle =
    "border-2 border-[#002FD4] text-[#002FD4] hover:bg-[#002FD4] hover:text-white";

  // const defaultButtonStyle =
  //   "border-2 border-[#002FD4] text-[#002FD4] hover:bg-[#002FD4] hover:text-white";

  if (isFull) {
    buttonText = "Seats Full";
    buttonDisabled = true;
    buttonStyle =
      "bg-gray-300 text-gray-500 cursor-not-allowed border-gray-300";
  } else if (alreadyRegistered) {
    if (canJoinNow) {
      buttonText = "Join Now";
      buttonDisabled = false;
      buttonStyle = defaultButtonStyle;
    } else {
      buttonText = "Join";
      buttonDisabled = true;
      buttonStyle = "bg-gray-300 text-gray-500 cursor-not-allowed";
    }
  } else {
    // Not registered
    if (isFree) {
      buttonText = "Register (Free)";
    } else {
      buttonText = "Register";
    }

    buttonDisabled = false;
    buttonStyle = defaultButtonStyle;
  }

  return (
    <div className="bg-white rounded-lg border border-[#E4E5ED] p-6 hover:shadow-md transition-shadow">
      {/* Healthcare Provider Profile - Centered at top */}
      <div className="flex flex-col items-center mb-4">
        <img
          src={webinar.doctorImage}
          alt={webinar.doctorName}
          className="w-20 h-20 rounded-full object-cover border-4 border-[#F4F6F9] mb-3"
        />
        <h3 className="font-poppins font-bold text-[16px] leading-[24px] text-[#0F1011] mb-1">
          {webinar.doctorName}
        </h3>
      </div>

      {/* Webinar Title - Rectangular tag with rounded corners, centered */}
      <div className="mb-4 flex justify-center">
        <div className="px-4 py-2 bg-[#F4F6F9] rounded-lg">
          <h4 className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011] text-center">
            {webinar.title}
          </h4>
        </div>
      </div>

      {/* Details - Two Column Layout */}
      <div className="mb-6">
        {/* First Row - Date and Time side by side */}
        <div className="grid grid-cols-2 gap-4 mb-3">
          <div className="flex items-center gap-2">
            <CalendarIcon size={16} weight="bold" color="#64748B" />
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.date}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ClockIcon size={16} weight="bold" color="#64748B" />
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.time}
            </span>
          </div>
        </div>

        {/* Second Row - Duration */}
        <div className="mb-3">
          <div className="flex items-center gap-2">
            <ClockIcon size={16} weight="bold" color="#64748B" />
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.duration}
            </span>
          </div>
        </div>

        {/* Third Row - Capacity */}
        <div className="flex items-center gap-2">
          <UsersIcon size={16} weight="bold" color="#64748B" />
          <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
            {webinar.capacity.filled} / {webinar.capacity.total} filled
          </span>
        </div>
      </div>

      {/* Price and Action Button - Bottom */}
      <div className="flex items-center justify-between pt-4 border-t border-[#E4E5ED]">
        <div>
          {webinar.price === null ? (
            <span className="px-3 py-1 bg-[#E8F0FE] text-[#002FD4] rounded-full font-poppins font-semibold text-[12px] leading-[16px]">
              Free
            </span>
          ) : (
            <span className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011]">
              {formatFee(webinar.price, webinar.currency)}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => {
            if (isFull) return;

            if (alreadyRegistered) {
              if (canJoinNow) {
                onJoin?.(webinar);
              }
              return;
            }

            // Not registered
            onRegister(webinar);
          }}
          disabled={isFull || buttonDisabled}
          className={`font-poppins font-semibold text-[14px] leading-[20px] py-2.5 px-6 rounded-md transition-colors ${
            isFull
              ? "bg-gray-300 text-gray-500 cursor-not-allowed border-gray-300"
              : buttonStyle
          }`}
        >
          {isFull ? "Seats Full" : buttonText}
        </button>
      </div>
    </div>
  );
};

export default WebinarCard;
