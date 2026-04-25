import { formatFee } from "@/utils/helper";
import {
  Calendar,
  Clock,
  Users,
  Trash,
  PencilSimple,
  Play,
} from "@phosphor-icons/react";
import { type FC } from "react";

interface WebinarItemProps {
  id: string;
  doctorName: string;
  specialty: string;
  title: string;
  date: string;
  time: string;
  duration: string;
  seats: string;
  price: string;
  currency?: string;
  type: "free" | "paid";
  imageUrl?: string | null;
  status?: string;
  onEdit?: () => void;
  onDelete?: () => void;
  onGoLive?: () => void;
}

export const WebinarItem: FC<WebinarItemProps> = ({
  doctorName,
  title,
  date,
  time,
  duration,
  seats,
  price,
  currency,
  type,
  imageUrl,
  status,
  onEdit,
  onDelete,
  onGoLive,
}) => {
  const isFree = type === "free";
  const FALLBACK_IMAGE = "/assets/icons/doctor-icon.svg";

  return (
    <div className="w-full max-w-sm bg-white rounded-2xl shadow-md overflow-hidden border border-gray-100">
      {/* Top Section - Avatar, Name, Status, Title */}
      <div className="p-6 text-center">
        {/* Avatar */}
        <div className="w-16 h-16 mx-auto rounded-full from-[#002FD4] to-[#0052FF] overflow-hidden">
          {imageUrl ? (
            <img
              src={imageUrl || FALLBACK_IMAGE}
              alt={doctorName || "Host"}
              className="w-full h-full object-cover rounded-full"
              onError={(e) => {
                e.currentTarget.src = FALLBACK_IMAGE;
                e.currentTarget.onerror = null;
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-white font-poppins font-bold text-2xl">
                {doctorName?.charAt(0)?.toUpperCase() || "H"}
              </span>
            </div>
          )}
        </div>

        {/* Healthcare Provider Name */}
        <h3 className="font-poppins font-medium text-sm text-[#0F1011] mt-3">
          {doctorName}
        </h3>

        {/* Status Badge */}
        {status && (
          <div className="mt-2">
            <span
              className={`inline-block px-3 py-1 rounded-full text-xs font-poppins font-semibold ${
                status === "scheduled"
                  ? "bg-[#E0EFFF] text-[#002FD4]"
                  : status === "live"
                    ? "bg-green-100 text-green-600"
                    : status === "completed"
                      ? "bg-gray-100 text-gray-600"
                      : status === "draft"
                        ? "bg-yellow-100 text-yellow-600"
                        : "bg-red-100 text-red-600"
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
          </div>
        )}

        {/* Title Badge */}
        <div className="mt-2">
          <span className="inline-block px-4 py-1.5 rounded-full bg-[#F4F6F9] text-[#0F1011] font-poppins text-sm">
            {title.length > 30 ? title.substring(0, 27) + "..." : title}
          </span>
        </div>
      </div>

      {/* Middle Section - Details */}
      <div className="px-6 pb-5 space-y-3">
        {/* Date and Time in one row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar size={18} weight="regular" className="text-[#002FD4]" />
            <span className="font-poppins text-sm text-[#0F1011]">{date}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={18} weight="regular" className="text-[#002FD4]" />
            <span className="font-poppins text-sm text-[#0F1011]">{time}</span>
          </div>
        </div>

        {/* Duration */}
        <div className="flex items-center gap-2">
          <Clock size={18} weight="regular" className="text-[#002FD4]" />
          <span className="font-poppins text-sm text-[#0F1011]">
            {duration}
          </span>
        </div>

        {/* Capacity */}
        <div className="flex items-center gap-2">
          <Users size={18} weight="regular" className="text-[#002FD4]" />
          <span className="font-poppins text-sm text-[#0F1011]">{seats}</span>
        </div>
      </div>

      {/* Bottom Section - Price and Action Buttons */}
      <div className="px-6 pb-6">
        {/* Price/Free Badge */}
        <div className="mb-3">
          {isFree ? (
            <span className="inline-block px-4 py-1.5 rounded-lg bg-[#002FD433] text-[#002FD4] font-poppins font-semibold text-sm">
              Free
            </span>
          ) : (
            <span className="font-poppins font-semibold text-lg text-[#0F1011]">
              {formatFee(price, currency)}
            </span>
          )}
        </div>

        {/* Go Live Button */}
        {onGoLive && status !== "completed" && status !== "cancelled" && (
          <button
            onClick={onGoLive}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 mb-2 rounded-md bg-[#002FD4] text-white hover:bg-[#002bb8] transition-colors"
          >
            <Play size={16} weight="fill" />
            <span className="font-poppins font-semibold text-sm">Go Live</span>
          </button>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Edit Button */}
          {onEdit && status !== "completed" && (
            <button
              onClick={onEdit}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md border border-[#002FD4] bg-white text-[#002FD4] hover:bg-[#F0F5FF] transition-colors"
            >
              <PencilSimple size={16} weight="bold" />
              <span className="font-poppins font-semibold text-sm">Edit</span>
            </button>
          )}

          {/* Delete Button */}
          {onDelete && (
            <button
              onClick={onDelete}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md border border-[#EF4444] bg-white text-[#EF4444] hover:bg-[#FEF2F2] transition-colors"
            >
              <Trash size={16} weight="bold" />
              <span className="font-poppins font-semibold text-sm">Delete</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
