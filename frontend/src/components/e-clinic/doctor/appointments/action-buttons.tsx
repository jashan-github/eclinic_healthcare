// action-buttons.tsx
import { UploadSimple } from "@phosphor-icons/react";
import { toast } from "react-toastify";
import { formatDate, formatFee, formatTime } from "@/utils/helper";
import AgoraVideoCallRoom from "../webinars/agora-video-call-room";
import { useState } from "react";
import { useJoinVideoSession } from "@/hooks/use-video-call";

interface ActionButtonsProps {
  id: string;
  timeSpan: number;
  timeSlot: string;
  timeEnd?: string;
  amount: number;
  currency: string;
  isTeleconsultation: boolean;
  canStartCall?: boolean;
  canUploadPrescription?: boolean;
  canReschedule?: boolean;
  appointmentId?: string;
  isAppointmentRequest?: boolean;
  date?: string;
  sessionId?: string | null;
  amount_before_waiver?: number;
  waiver_percent?: number;
}

export default function ActionButtons({
  // id,
  timeSpan,
  timeSlot,
  // timeEnd,
  amount,
  currency,
  isTeleconsultation,
  canStartCall,
  canUploadPrescription = false,
  // canReschedule = true,
  // appointmentId,
  isAppointmentRequest = false,
  date,
  amount_before_waiver,
  waiver_percent,

  sessionId,
}: ActionButtonsProps) {
  const [active, setActive] = useState(false);
  const [initialJoinData, setInitialJoinData] = useState<any>(null);
  const joinSession = useJoinVideoSession();

  const waiverPercent = waiver_percent ?? 0;
  const hasWaiver = waiverPercent > 0;

  const originalAmount = amount_before_waiver ?? amount;

  const handleStartCall = async (session_id: string | null) => {
    if (!session_id) {
      toast.error("Session ID missing");
      return;
    }

    try {
      const response = await joinSession.mutateAsync(session_id);

      if (response.data.both_ready && response.data.token) {
        // Both ready and token received - pass data to child
        setInitialJoinData(response.data);
        setActive(true);
      } else if (response.data.waiting_room) {
        // Show waiting room - pass partial data
        setInitialJoinData(response.data);
        setActive(true);
      } else {
        toast.info(response.data.message || "Waiting for other party...");
      }
    } catch {
      toast.error("Unable to start call");
    }
  };

  if (active && sessionId) {
    return (
      <AgoraVideoCallRoom
        sessionId={sessionId}
        initialJoinData={initialJoinData}
        onLeave={() => {
          setActive(false);
          setInitialJoinData(null);
          // Reload page to get fresh session
          window.location.reload();
        }}
      />
    );
  }

  return (
    <div className="flex items-center justify-between">
      {/* Time & Payment */}
      <div className="flex items-center gap-4 text-sm">
        <div className="inline-flex items-center divide-x divide-[#D1D1D1] border border-[#D1D1D1] rounded-md overflow-hidden">
          <div className="px-4 py-1.5">
            <span className="font-poppins font-medium text-sm text-[#0F1011]">
              {timeSpan} min
            </span>
          </div>
          <div className="px-4 py-1.5">
            <span className="font-poppins text-sm text-[#0F1011]">
              {date && formatDate(date)} {date && " at "} {formatTime(timeSlot)}
            </span>
          </div>
        </div>

        <div className="inline-flex items-center divide-x divide-[#D1D1D1] border border-[#D1D1D1] rounded-md overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-1.5">
            {!hasWaiver && (
              <>
                <span className="font-poppins text-sm text-[#0F1011]">
                  Amount :
                </span>
                <span className="font-poppins font-medium text-sm text-[#0F1011]">
                  {formatFee(amount, currency)}
                </span>
              </>
            )}

            {hasWaiver && (
              <>
                <span className="font-poppins text-sm text-[#64748B] line-through">
                  {formatFee(originalAmount, currency)}
                </span>

                <span className="text-[#64748B] text-sm">→</span>

                <span className="font-poppins font-medium text-sm text-[#0F1011]">
                  {formatFee(amount, currency)}
                </span>

                <span className="font-poppins text-[12px] text-green-600 font-medium">
                  ({waiverPercent}% off)
                </span>
              </>
            )}
          </div>
          <div className="px-4 py-1.5">
            <span
              className={`font-poppins font-medium text-sm ${isAppointmentRequest ? "text-red-600" : "text-green-600"}`}
            >
              {isAppointmentRequest ? "Unpaid" : "Paid"}
            </span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {isTeleconsultation && !isAppointmentRequest && canStartCall && (
          // <button
          //   onClick={handleStartCall}
          //   disabled={!canStartCall || startingCall}
          //   className={`flex items-center gap-2 px-5 py-2.5 text-sm rounded-md font-medium transition ${canStartCall && !startingCall
          //     ? 'bg-[#002FD4] text-white hover:bg-[#0020b0]'
          //     : 'bg-gray-200 text-gray-500 cursor-not-allowed'
          //     }`}
          // >
          //   <span className="font-poppins">
          //     {startingCall ? 'Starting...' : 'Start Call'}
          //   </span>
          // </button>
          <button
            onClick={() => handleStartCall(sessionId ?? null)}
            disabled={!canStartCall}
            className={`flex items-center gap-2 px-5 py-2.5 text-sm rounded-md font-medium transition ${
              canStartCall
                ? "bg-[#002FD4] text-white hover:bg-[#0020b0]"
                : "bg-gray-200 text-gray-500 cursor-not-allowed"
            }`}
          >
            Start Call
          </button>
        )}
        <button
          disabled={!canUploadPrescription}
          className={`flex items-center gap-1.5 px-4 py-2.5 text-sm rounded-md transition ${
            canUploadPrescription
              ? "bg-[#F4F4F4] hover:bg-[#eaeaea]"
              : "bg-gray-100 text-gray-600 cursor-not-allowed"
          }`}
        >
          <UploadSimple size={16} />
          <span className="font-poppins text-[13px]">Upload Prescription</span>
        </button>

        {/* Reschedule button */}
        {/* <button
  disabled={!canReschedule}
  className={`px-5 py-2 text-sm rounded-md border font-medium transition ${canReschedule
      ? 'border-[#002FD4] text-[#002FD4] hover:bg-[#002FD4]/5'
      : 'border-gray-300 text-gray-400 cursor-not-allowed'
    }`}
>
  Reschedule
</button> */}
      </div>
    </div>
  );
}
