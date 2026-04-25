// src/components/e-clinic/doctor/appointments/today-appointments.tsx
import {
  MapPinIcon,
  VideoCameraIcon,
  StethoscopeIcon,
} from "@phosphor-icons/react";
import { type FC, type ReactElement } from "react";
import ActionButtons from "./action-buttons";

interface TodayAppointmentProps {
  id?: string;
  name: string;
  gender: "M" | "F";
  age: number;
  image: string;
  isInClinic: boolean;
  timeSpan: number;
  timeSlot: string;
  timeEnd?: string;
  amount: number;
  currency: string;
  paymentMode?: string;
  canStartCall?: boolean;
  appointmentId?: string;
  isAppointmentRequest?: boolean;
  date?: string;
  sessionId?: string | null;
  amount_before_waiver?: number;
  waiver_percent?: number;
  serviceName?: string;
}

const TodayAppointment: FC<TodayAppointmentProps> = ({
  id,
  name,
  gender,
  age,
  image,
  isInClinic,
  timeSpan,
  timeSlot,
  timeEnd,
  amount,
  currency,
  canStartCall = false,
  appointmentId,
  isAppointmentRequest = false,
  date,
  sessionId,
  amount_before_waiver,
  waiver_percent,
  serviceName,
}): ReactElement => {
  const FALLBACK_IMAGE = "/assets/icons/doctor-icon.svg";
  // console.log("appointmentId",appointmentId)
  return (
    <div className="rounded-md p-4 border border-[#E8E8E8] bg-white">
      <div className="flex flex-col gap-5">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className=" bg-[#E8EEFD] rounded-full">
              <img
                src={image || FALLBACK_IMAGE}
                alt={FALLBACK_IMAGE}
                className="w-16 h-16 rounded-full object-cover"
                onError={(e) => {
                  e.currentTarget.src = FALLBACK_IMAGE;
                  e.currentTarget.onerror = null;
                }}
              />
            </div>
            <div className="flex flex-col">
              <div className="font-poppins font-bold text-sm text-[#0F1011]">
                {name} | {gender} | {age}y
              </div>

              {serviceName && (
                <div
                  className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full 
                 bg-[#EEF2FF] text-[#1E40AF] max-w-fit"
                  title={serviceName}
                >
                  <StethoscopeIcon size={14} weight="bold" />
                  <span className="font-poppins text-[12px] font-medium truncate max-w-[200px]">
                    {serviceName}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center">
            <div className="flex items-center gap-2 px-3 py-2 rounded-md border border-[#E8E8E8] bg-white">
              {isInClinic ? (
                <MapPinIcon size={16} color="#002FD4" weight="fill" />
              ) : (
                <VideoCameraIcon size={18} color="#002FD4" weight="fill" />
              )}
              <span className="font-poppins text-[13px] text-[#0F1011]">
                {isInClinic ? "In-clinic" : "Teleconsultation"}
              </span>
            </div>
          </div>
        </div>

        <ActionButtons
          id={id ? id : ""}
          timeSpan={timeSpan}
          timeSlot={timeSlot}
          timeEnd={timeEnd}
          date={date}
          amount={amount}
          currency={currency}
          isTeleconsultation={!isInClinic}
          canStartCall={canStartCall}
          appointmentId={appointmentId}
          isAppointmentRequest={isAppointmentRequest}
          sessionId={sessionId}
          amount_before_waiver={amount_before_waiver}
          waiver_percent={waiver_percent}
        />
      </div>
    </div>
  );
};

export default TodayAppointment;
