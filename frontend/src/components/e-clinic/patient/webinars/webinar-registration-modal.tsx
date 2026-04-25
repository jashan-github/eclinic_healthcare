import {
  CalendarIcon,
  ClockIcon,
  UsersIcon,
  CurrencyDollarIcon,
} from "@phosphor-icons/react";
import Modal from "@/components/ui/modal";
import type { UserRoleType } from "@/utils/user-role";
import { formatFee } from "@/utils/helper";
import { useAuth } from "@/context/auth/auth-context-utils";

export interface AdminWebinarHost {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  role: UserRoleType;
  education?: string;
  years_of_experience?: number;
  specialty?: string;
}

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
  host?: AdminWebinarHost;
  price: number | null;
  doctorExperience?: string;
  doctorDescription?: string;
  webinarDescription?: string;
  currency?: string;
}

interface WebinarRegistrationModalProps {
  webinar: Webinar | null;
  isOpen: boolean;
  onClose: () => void;
  onRegister: (webinarId: string) => void;
  is_registered?: boolean;
  can_join?: boolean;
  hostId?: string;
  onJoinWebinar?: () => void;
}

const WebinarRegistrationModal = ({
  webinar,
  isOpen,
  onClose,
  onRegister,
  is_registered = false,
  can_join = false,
  hostId,
  onJoinWebinar,
}: WebinarRegistrationModalProps) => {
  const { user } = useAuth();
  if (!webinar) return null;

  const remainingSeats = webinar.capacity.total - webinar.capacity.filled;

  const isHost = hostId === user?.id;

  const handleAction = () => {
    if (isHost || is_registered) {
      if (can_join && onJoinWebinar) {
        onJoinWebinar();
      }
      // else: do nothing or show toast "not yet started"
    } else {
      onRegister(webinar.id);
    }
  };

  const buttonText =
    isHost || is_registered
      ? can_join
        ? "Join Now"
        : "Join (Not Started)"
      : webinar.price === null
        ? "Register for Free"
        : `Register for ${formatFee(webinar.price, webinar.currency)}`;

  const isDisabled = (isHost || is_registered) && !can_join;

  const footer = (
    <>
      <button
        type="button"
        onClick={handleAction}
        disabled={isDisabled}
        className={`px-6 py-2.5 font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors
          ${
            isDisabled
              ? "bg-[#002FD4] text-white opacity-50 cursor-not-allowed"
              : "bg-[#002FD4] hover:bg-[#001FB8] text-white"
          }`}
      >
        {buttonText}
      </button>
      <button
        type="button"
        onClick={onClose}
        className="px-6 py-2.5 bg-white border border-[#E4E5ED] hover:bg-[#F4F6F9] text-[#0F1011] font-poppins font-semibold text-[14px] leading-[20px] rounded-md transition-colors"
      >
        Cancel
      </button>
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={webinar.title}
      footer={footer}
      maxWidth="2xl"
    >
      {/* Healthcare Provider Information */}
      <div className="flex items-start gap-4 mb-6">
        <img
          src={webinar.doctorImage}
          alt={webinar.doctorName}
          className="w-20 h-20 rounded-full object-cover border-4 border-[#F4F6F9] flex-shrink-0"
        />
        <div className="flex-1">
          <h3 className="font-poppins font-bold text-[18px] leading-[24px] text-[#0F1011] mb-1">
            Dr. {webinar.doctorName}
            {webinar.host?.education && (
              <span className="font-medium text-[#64748B]">
                {" "}
                ({webinar.host.education})
              </span>
            )}
          </h3>
          {/* <div className="flex flex-wrap items-center gap-2 mt-2">
            {webinar.doctorSpecialty && (
              <span className="px-3 py-1 text-[12px] font-medium rounded-full bg-[#EEF2FF] text-[#002FD4]">
                {webinar.doctorSpecialty}
              </span>
            )}

            {webinar.doctorExperience && (
              <span className="flex items-center gap-1 text-[13px] text-[#64748B] font-medium">
                <PersonIcon size={14} weight="bold" />
                {webinar.doctorExperience}
              </span>
            )}
          </div> */}
          {webinar.host?.specialty && (
            <p className="mt-1 text-[14px] font-medium text-[#002FD4]">
              {webinar.host.specialty}
            </p>
          )}

          {/* Experience */}
          {typeof webinar.host?.years_of_experience === "number" && (
            <p className="mt-1 text-[13px] text-[#64748B]">
              {webinar.host.years_of_experience} years of experience
            </p>
          )}
        </div>
      </div>

      {/* About this webinar */}
      {webinar.webinarDescription && (
        <div className="mb-6">
          <h4 className="font-poppins font-semibold text-[16px] leading-[24px] text-[#0F1011] mb-3">
            About this webinar
          </h4>
          <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
            {webinar.webinarDescription}
          </p>
        </div>
      )}

      {/* Webinar Details - Two column grid layout matching image */}
      <div className="grid grid-cols-2 gap-4">
        {/* Row 1, Left: Date */}
        <div className="flex items-start gap-2">
          <CalendarIcon
            size={20}
            weight="bold"
            color="#64748B"
            className="flex-shrink-0 mt-0.5"
          />
          <div className="flex flex-col">
            <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
              Date
            </span>
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.date}
            </span>
          </div>
        </div>

        {/* Row 1, Right: Seats Available */}
        <div className="flex items-start gap-2">
          <UsersIcon
            size={20}
            weight="bold"
            color="#64748B"
            className="flex-shrink-0 mt-0.5"
          />
          <div className="flex flex-col">
            <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
              Seats Available
            </span>
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {remainingSeats} of {webinar.capacity.total} remaining
            </span>
          </div>
        </div>

        {/* Row 2, Left: Time & Duration */}
        <div className="flex items-start gap-2">
          <ClockIcon
            size={20}
            weight="bold"
            color="#64748B"
            className="flex-shrink-0 mt-0.5"
          />
          <div className="flex flex-col">
            <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
              Time & Duration
            </span>
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.time} • {webinar.duration}
            </span>
          </div>
        </div>

        {/* Row 2, Right: Fee */}
        <div className="flex items-start gap-2">
          <CurrencyDollarIcon
            size={20}
            weight="bold"
            color="#64748B"
            className="flex-shrink-0 mt-0.5"
          />
          <div className="flex flex-col">
            <span className="font-poppins font-semibold text-[14px] leading-[20px] text-[#0F1011]">
              Fee
            </span>
            <span className="font-poppins font-normal text-[14px] leading-[20px] text-[#0F1011]">
              {webinar.price === null ? (
                <span className="text-[#002FD4] font-semibold">Free</span>
              ) : (
                <span>{formatFee(webinar.price, webinar.currency)}</span>
              )}
            </span>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default WebinarRegistrationModal;
